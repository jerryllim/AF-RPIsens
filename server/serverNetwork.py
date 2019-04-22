import zmq
import json
import datetime
import socket
import threading
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler


class NetworkManager:
    router_send = None
    router_recv = None
    self_add = None
    scheduler = None
    scheduler_jobs = {}

    def __init__(self, settings, database_manager):
        self.self_add = self.get_ip_add()
        self.context = zmq.Context()
        self.settings = settings
        self.database_manager = database_manager
        self.router_routine()
        self.setup_router_send()
        self.router_kill = threading.Event()
        self.router_thread = threading.Thread(target=self.route)
        self.router_thread.daemon = True
        self.router_thread.start()
        self.scheduler = BackgroundScheduler()
        jam_dur = self.settings.config.getint('Network', 'interval')
        self.schedule_jam(interval=jam_dur)
        self.scheduler.start()

    def setup_router_send(self):
        if self.router_send:
            self.router_send.close()
        self.router_send = self.context.socket(zmq.ROUTER)
        self.router_send.setsockopt(zmq.LINGER, 0)
        # connect to all the ports
        for ip, port in self.settings.get_ips_ports():
            self.router_send.connect("tcp://{}:{}".format(ip, port))

    def request(self, id_to, msg):
        temp_dict = {}
        to_send = [id_to.encode(), (json.dumps(msg)).encode()]
        self.router_send.send_multipart(to_send)

        now = datetime.datetime.now().isoformat()

        if self.router_send.poll(2000):
            try:
                id_from, recv_bytes = self.router_send.recv_multipart()
                temp_dict.update(json.loads(recv_bytes.decode()))
                temp_dict['ip'] = id_from
            except IOError as error:
                print("{} Problem with socket: ".format(now), error)
        else:
            print("{} Machine ({}) is not connected".format(now, id_to))

        return temp_dict

    def router_routine(self):
        port_number = "{}:{}".format(self.self_add, self.settings.config.get('Network', 'port'))
        self.router_recv = self.context.socket(zmq.ROUTER)
        self.router_recv.bind("tcp://%s" % port_number)

    def route(self):
        while not self.router_kill.is_set():
            poller = zmq.Poller()
            poller.register(self.router_recv, zmq.POLLIN)

            poll = poller.poll(1000)  # Wait for one second
            if poll:
                ident = self.router_recv.recv()  # routing information
                delimiter = self.router_recv.recv()  # delimiter
                message = self.router_recv.recv_json()
                reply_dict = {}

                for key in message.keys():
                    if key == "job_info":
                        barcode = message.get("job_info", None)
                        reply_dict[barcode] = self.database_manager.get_job_info(barcode)
                    elif key == "sfu":
                        print(message.get("sfu", None))
                    elif key == "ink_key":
                        ink_key = message.get("ink_key", None)
                        self.database_manager.replace_ink_key(ink_key)

                self.router_recv.send(ident, zmq.SNDMORE)
                self.router_recv.send(delimiter, zmq.SNDMORE)
                self.router_recv.send_json(reply_dict)

    def request_jam(self):
        print("Requesting jam at {}".format(datetime.datetime.now().isoformat()))
        for ip, port in self.settings.get_ips_ports():
            msg_dict = {"jam": 0}
            deal_msg = self.request(ip, msg_dict)

            machine_ip = deal_msg.get('ip')
            # machine = self.settings.get_machine(machine_ip)

            jam_msg = deal_msg.pop('jam', {})
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

    def send_job_info(self):
        # TODO retrive mac from server settings
        for ip in self.settings.get_ips():
            mac = self.settings.get_mac(ip)
            job_list = self.database_manager.get_jobs_for(mac)
            self.request(ip, {'job_info': job_list})

    def schedule_jam(self, interval=5):
        cron_trigger = CronTrigger(minute='*/{}'.format(interval))
        job_id = 'JAM'
        if self.scheduler_jobs.get(job_id):
            self.scheduler_jobs[job_id].remove()
        self.scheduler_jobs[job_id] = self.scheduler.add_job(self.request_jam, cron_trigger, id=job_id,
                                                             misfire_grace_time=30, max_instances=3)

    @staticmethod
    def get_ip_add():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_add = s.getsockname()[0]
        s.close()

        return ip_add


if __name__ == '__main__':
    pass
    # NetworkManager()
