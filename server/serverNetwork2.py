import os
import csv
import zmq
import json
import time
import socket
import logging
import datetime
import threading
import serverDatabase
import multiprocessing
from io import StringIO
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler


class NetworkManager:
    router_send = None
    self_add = None
    scheduler = None
    scheduler_jobs = {}

    def __init__(self, settings, db_dict):
        # Logger setup
        self.logger = logging.getLogger('jamSERVER')
        self.logger.setLevel(logging.DEBUG)
        path = os.path.expanduser('~/Documents/JAM/JAMserver/jamSERVER.log')
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(logging.DEBUG)
        log_format = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s: %(module)s - %(message)s')
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)
        self.logger.info('\n\nStarted logging')
        ap_logger = logging.getLogger('apscheduler')
        ap_logger.setLevel(logging.DEBUG)
        ap_logger.addHandler(file_handler)

        # multiprocessing.set_start_method("spawn")
        self.self_add = self.get_ip_add()
        self.context = zmq.Context()
        self.settings = settings
        self.database_manager = serverDatabase.DatabaseManager(settings, **db_dict)
        self.setup_router_send()
        self.router_kill = threading.Event()
        self.respond_process = RespondentProcess(self.self_add, db_dict)
        self.respond_process.daemon = True
        self.respond_process.start()
        self.sender_thread = threading.Thread(target=self.router_send_loop)
        self.sender_thread.daemon = True
        self.sender_thread.start()
        self.scheduler = BackgroundScheduler()
        jam_dur = self.settings.config.getint('Network', 'interval')
        self.schedule_jam(interval=jam_dur)
        self.scheduler.start()
        self.logger.info('Completed serverNetwork __init__')

    def setup_router_send(self):
        if self.router_send:
            self.router_send.close()
        self.router_send = self.context.socket(zmq.ROUTER)
        self.router_send.setsockopt(zmq.LINGER, 0)
        self.router_send.setsockopt(zmq.IMMEDIATE, 1)
        self.router_send.setsockopt(zmq.TCP_KEEPALIVE, 1)
        self.router_send.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 1)
        self.router_send.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
        self.router_send.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
        self.router_send.setsockopt(zmq.ROUTER_MANDATORY, 1)
        self.router_send.setsockopt(zmq.ROUTER_HANDOVER, 1)
        # connect to all the ports
        for ip, port in self.settings.get_ips_ports():
            self.router_send.connect("tcp://{}:{}".format(ip, port))

    def request(self, id_to, msg):
        temp_dict = {}
        to_send = [id_to.encode(), (json.dumps(msg)).encode()]
        try:
            self.router_send.send_multipart(to_send)
        except zmq.ZMQError as error:
            self.logger.warning("Error {} for ip {}".format(error, id_to))

        now = datetime.datetime.now().isoformat()

        if self.router_send.poll(2000):
            try:
                id_from, recv_bytes = self.router_send.recv_multipart()
                temp_dict.update(json.loads(recv_bytes.decode()))
                temp_dict['ip'] = id_from.decode()
            except IOError as error:
                self.logger.debug("{} Problem with socket: {}".format(now, error))
        else:
            self.logger.debug("{} Machine ({}) is not connected".format(now, id_to))
            port = self.settings.get_port_for(id_to)
            self.router_send.connect("tcp://{}:{}".format(id_to, port))

        return temp_dict

    def router_routine(self):
        port_number = "{}:{}".format(self.self_add, self.settings.config.get('Network', 'port'))
        self.router_recv = self.context.socket(zmq.ROUTER)
        self.router_recv.setsockopt(zmq.IMMEDIATE, 1)
        self.router_recv.setsockopt(zmq.TCP_KEEPALIVE, 1)
        self.router_recv.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 1)
        self.router_recv.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
        self.router_recv.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
        self.router_recv.setsockopt(zmq.ROUTER_MANDATORY, 1)
        self.router_recv.setsockopt(zmq.ROUTER_HANDOVER, 1)
        self.router_recv.bind("tcp://%s" % port_number)

    def route(self):
        while not self.router_kill.is_set():
            if self.router_recv.poll(100):
                id_from, recv_msg = self.router_recv.recv_multipart()
                ip = id_from.decode()
                message = json.loads(recv_msg.decode())
                # ip = message.get("ip", None)
                self.logger.debug("Received message {} from {}".format(message, ip))
                reply_dict = {}

                for key in message.keys():
                    if key == "job_info":
                        barcode = message.get("job_info", None)
                        reply_dict[barcode] = self.database_manager.get_job_info(barcode)
                    elif key == "sfu":
                        sfu_str = message.get("sfu", None)
                        if sfu_str:
                            self.insert_sfu(ip, sfu_str)
                    elif key == "ping":
                        reply_dict["pong"] = 1

                self.database_manager.update_ludt_fr(ip)
                self.logger.debug("Replying with {}".format(reply_dict))
                self.router_recv.send_multipart([id_from, (json.dumps(reply_dict)).encode()])
                # self.router_recv.send(ident, zmq.SNDMORE)
                # self.router_recv.send(delimiter, zmq.SNDMORE)
                # self.router_recv.send_json(reply_dict)

    def worker_talk(self, msg="jam"):
        sender = self.context.socket(zmq.DEALER)
        sender.connect("inproc://send.ipc")
        sender.send_string(msg)

    def router_send_loop(self):
        worker = self.context.socket(zmq.DEALER)
        worker.setsockopt_string(zmq.IDENTITY, "SendWorker")
        worker.bind("inproc://send.ipc")

        poller = zmq.Poller()
        poller.register(self.router_send, zmq.POLLIN)
        poller.register(worker, zmq.POLLIN)

        while not self.router_kill.is_set():
            socks = dict(poller.poll(1000))

            if self.router_send in socks:
                id_from, recv_bytes = self.router_send.recv_multipart()
                recv_dict = json.loads(recv_bytes.decode())
                machine_ip = id_from.decode()

                if recv_dict.pop("jobs", 0):
                    self.database_manager.update_ludt_jobs(machine_ip)

                jam_msg = recv_dict.pop('jam', {})
                sfu_list = jam_msg.pop('sfu', [])
                for sfu_str in sfu_list:
                    self.insert_sfu(machine_ip, sfu_str)

                for idx in range(1, 4):
                    machine = self.settings.get_machine(machine_ip, idx)
                    qc_list = jam_msg.pop('Q{}'.format(idx), [])
                    if qc_list:
                        self.database_manager.insert_qc(machine, qc_list)
                    maintenance_dict = jam_msg.pop('M{}'.format(idx), {})
                    if maintenance_dict:
                        self.database_manager.replace_maintenance(machine, maintenance_dict)
                    emp_dict = jam_msg.pop('E{}'.format(idx), {})
                    if emp_dict:
                        self.database_manager.replace_emp_shift(machine, emp_dict)

                self.database_manager.insert_jam(machine_ip, jam_msg)

            if worker in socks:
                recv_msg = str(worker.recv(), "utf-8")

                if recv_msg == "jam":
                    ip_list = self.settings.get_ips()
                    error_list = []
                    for ip in ip_list:
                        send_dict = {'jam': 0}
                        jobs = self.get_jobs_info_for(ip)
                        if jobs:
                            send_dict['jobs'] = jobs
                        to_send = [ip.encode(), (json.dumps(send_dict)).encode()]
                        try:
                            self.router_send.send_multipart(to_send)
                        except zmq.ZMQError as error:
                            error_list.append(ip)
                            self.logger.warning("Error {} for ip {}".format(error, ip))

                    time.sleep(1)

    def insert_sfu(self, ip, sfu_str):
        sfu_list = json.loads(sfu_str)
        umc = self.database_manager.get_umc_for(sfu_list[0], sfu_list[1])
        idx = sfu_list[2]
        sfu_list[2] = self.settings.get_mac(ip, idx)
        sfu_list = [umc] + sfu_list

        self.database_manager.insert_sfu(sfu_list)
        self.database_manager.update_job(sfu_list[1], sfu_list[2], sfu_list[4])

    def request_jam(self):
        now = datetime.datetime.now().isoformat()
        self.logger.debug("Requesting jam")
        ip_list = self.settings.get_ips()
        error_list = []
        for ip in ip_list:
            send_dict = {'jam': 0}
            jobs = self.get_jobs_info_for(ip)
            if jobs:
                send_dict['jobs'] = jobs
            to_send = [ip.encode(), (json.dumps(send_dict)).encode()]
            try:
                self.router_send.send_multipart(to_send)
            except zmq.ZMQError as error:
                error_list.append(ip)
                self.logger.warning("Error {} for ip {}".format(error, ip))

        time.sleep(1)

        while self.router_send.poll(2000):
            try:
                id_from, recv_bytes = self.router_send.recv_multipart()
                recv_dict = json.loads(recv_bytes.decode())
                machine_ip = id_from.decode()

                if machine_ip in ip_list:  # Otherwise raises ValueError
                    ip_list.remove(machine_ip)

                # machine = self.settings.get_machine(machine_ip)

                if recv_dict.pop("jobs", 0):
                    self.database_manager.update_ludt_jobs(machine_ip)

                jam_msg = recv_dict.pop('jam', {})
                sfu_list = jam_msg.pop('sfu', [])
                for sfu_str in sfu_list:
                    self.insert_sfu(machine_ip, sfu_str)

                for idx in range(1, 4):
                    machine = self.settings.get_machine(machine_ip, idx)
                    qc_list = jam_msg.pop('Q{}'.format(idx), [])
                    if qc_list:
                        self.database_manager.insert_qc(machine, qc_list)
                    maintenance_dict = jam_msg.pop('M{}'.format(idx), {})
                    if maintenance_dict:
                        self.database_manager.replace_maintenance(machine, maintenance_dict)
                    emp_dict = jam_msg.pop('E{}'.format(idx), {})
                    if emp_dict:
                        self.database_manager.replace_emp_shift(machine, emp_dict)

                self.database_manager.insert_jam(machine_ip, jam_msg)

            except IOError as error:
                self.logger.error("Problem with socket: {}".format(now, error))

        if ip_list:
            self.logger.info('Machine(s) {} did not reply.'.format(ip_list))

        for ip in error_list:
            port = self.settings.get_port_for(ip)
            self.router_send.connect("tcp://{}:{}".format(ip, port))
            self.logger.info("Reconnecting to {}:{}".format(ip, port))

    def send_job_info(self):
        # TODO retrive mac from server settings
        for ip in self.settings.get_ips():
            jobs = self.get_jobs_info_for(ip)
            reply = self.request(ip, {'jobs_list': jobs})

            if reply is not None:
                self.database_manager.update_ludt_jobs(ip)

    def get_jobs_info_for(self, ip):
        mac = self.settings.get_macs(ip)
        ludt_jobs = self.database_manager.get_last_updates(ip)[2]
        if not ludt_jobs:
            dt = None
        else:
            dt = ludt_jobs.strftime("%Y-%m-%d")

        jobs_list = self.database_manager.get_jobs_for_in(mac, dt)
        jobs_str = StringIO()
        csv_writer = csv.writer(jobs_str)
        csv_writer.writerows(jobs_list)
        jobs_str.seek(0)

        return jobs_str.getvalue()

    def schedule_jam(self, interval=5):
        cron_trigger = CronTrigger(minute='*/{}'.format(interval))
        job_id = 'JAM'
        if self.scheduler_jobs.get(job_id):
            self.scheduler_jobs[job_id].remove()
        self.scheduler_jobs[job_id] = self.scheduler.add_job(self.worker_talk, cron_trigger, id=job_id,
                                                             misfire_grace_time=30, max_instances=3)

    @staticmethod
    def get_ip_add():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_add = s.getsockname()[0]
        s.close()

        return ip_add


class RespondentProcess(multiprocessing.Process):
    router_recv = None

    def __init__(self, self_add, db_dict):
        multiprocessing.Process.__init__(self)
        # Logger setup
        self.logger = logging.getLogger('jamSERVER_respond')
        self.logger.setLevel(logging.DEBUG)
        path = os.path.expanduser('~/Documents/JAM/JAMserver/jamSERVER_respondent.log')
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(logging.DEBUG)
        log_format = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s: %(module)s - %(message)s')
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)
        self.logger.info('\n\nStarted logging')

        self.self_add = self_add
        self.context = zmq.Context()
        self.exit = multiprocessing.Event()
        self.settings = serverDatabase.Settings(log_name='jamSERVER_respond')
        self.database_manager = serverDatabase.DatabaseManager(self.settings, **db_dict, log_name='jamSERVER_respond')
        self.router_routine()

    def router_routine(self):
        port_number = "{}:{}".format(self.self_add, self.settings.config.get('Network', 'port'))
        self.router_recv = self.context.socket(zmq.ROUTER)
        self.router_recv.setsockopt(zmq.IMMEDIATE, 1)
        self.router_recv.setsockopt(zmq.TCP_KEEPALIVE, 1)
        self.router_recv.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 1)
        self.router_recv.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
        self.router_recv.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
        # self.router_recv.setsockopt(zmq.ROUTER_MANDATORY, 1)
        self.router_recv.setsockopt(zmq.ROUTER_HANDOVER, 1)
        self.router_recv.bind("tcp://%s" % port_number)

    def run(self):
        while not self.exit.is_set():
            self.logger.debug("Looping through")
            if self.router_recv.poll(100):
                self.logger.debug("Polled {}".format(self.router_recv.poll(1)))
                id_from, recv_msg = self.router_recv.recv_multipart()
                ip = id_from.decode()
                message = json.loads(recv_msg.decode())
                # ip = message.get("ip", None)
                if "quit" in message.keys():
                    break
                self.logger.debug("Received message {} from {}".format(message, ip))
                reply_dict = {}

                for key in message.keys():
                    if key == "job_info":
                        barcode = message.get("job_info", None)
                        reply_dict[barcode] = self.database_manager.get_job_info(barcode)
                    elif key == "sfu":
                        sfu_str = message.get("sfu", None)
                        if sfu_str:
                            self.insert_sfu(ip, sfu_str)
                    elif key == "ping":
                        reply_dict["pong"] = 1

                self.database_manager.update_ludt_fr(ip)
                self.logger.debug("Replying with {}".format(reply_dict))
                self.router_recv.send_multipart([id_from, (json.dumps(reply_dict)).encode()])

    def insert_sfu(self, ip, sfu_str):
        sfu_list = json.loads(sfu_str)
        umc = self.database_manager.get_umc_for(sfu_list[0], sfu_list[1])
        idx = sfu_list[2]
        sfu_list[2] = self.settings.get_mac(ip, idx)
        sfu_list = [umc] + sfu_list

        self.database_manager.insert_sfu(sfu_list)
        self.database_manager.update_job(sfu_list[1], sfu_list[2], sfu_list[4])


if __name__ == '__main__':
    pass
    # NetworkManager()
