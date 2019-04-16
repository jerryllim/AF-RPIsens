import zmq
import json
import datetime
import socket
import threading
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler


class NetworkManager:
    dealer = None
    dealers = {}
    router = None
    self_add = None
    scheduler = None
    scheduler_jobs = {}

    def __init__(self, settings, database_manager):
        self.self_add = self.get_ip_add()
        self.context = zmq.Context()
        self.settings = settings
        self.database_manager = database_manager
        self.router_routine()
        self.dealer_routine()
        self.router_kill = threading.Event()
        self.router_thread = threading.Thread(target=self.route)
        self.router_thread.daemon = True
        self.router_thread.start()
        self.scheduler = BackgroundScheduler()
        jam_dur = self.settings.config.getint('Network', 'interval')
        self.schedule_jam(interval=jam_dur)
        self.scheduler.start()

    def dealer_routine(self):
        self.dealer = self.context.socket(zmq.DEALER)
        self.dealer.setsockopt(zmq.LINGER, 0)
        self.set_up_dealers()

    def request2(self, port, msg):
        temp_dict = {}
        self.dealer.connect("tcp://{}".format(port))
        msg_json = json.dumps(msg)
        self.dealer.send_string("", zmq.SNDMORE)  # delimiter
        self.dealer.send_string(msg_json)

        # use poll for timeouts:
        poller = zmq.Poller()
        poller.register(self.dealer, zmq.POLLIN)

        socks = dict(poller.poll(2*1000))
        now = datetime.datetime.now().isoformat()

        if self.dealer in socks:
            try:
                self.dealer.recv()  # delimiter
                recv_msg = self.dealer.recv_json()
                temp_dict.update(recv_msg)
            except IOError as error:
                print("{} Problem with socket: ".format(now), error)
            finally:
                self.dealer.disconnect("tcp://{}".format(port))
        else:
            print("{} Machine ({}) is not connected".format(now, port))
            self.dealer.close()
            self.dealer_routine()

        return temp_dict

    def request(self, dealer, msg):
        temp_dict = {}
        msg_json = json.dumps(msg)
        dealer.send_string("", zmq.SNDMORE)  # delimiter
        dealer.send_string(msg_json)

        # use poll for timeouts:
        poller = zmq.Poller()
        poller.register(dealer, zmq.POLLIN)

        socks = dict(poller.poll(2*1000))
        now = datetime.datetime.now().isoformat()

        if dealer in socks:
            try:
                dealer.recv()  # delimiter
                recv_msg = self.dealer.recv_json()
                temp_dict.update(recv_msg)
            except IOError as error:
                print("{} Problem with socket: ".format(now), error)
        else:
            print("{} Machine ({}) is not connected".format(now, dealer.getsockopt_string(zmq.IDENTITY)))
            # self.dealer.close()
            # self.dealer_routine()

        return temp_dict

    def router_routine(self):
        port_number = "{}:{}".format(self.self_add, self.settings.config.get('Network', 'port'))
        self.router = self.context.socket(zmq.ROUTER)
        self.router.bind("tcp://%s" % port_number)

    def route(self):
        while not self.router_kill.is_set():
            poller = zmq.Poller()
            poller.register(self.router, zmq.POLLIN)

            poll = poller.poll(1000)  # Wait for one second
            if poll:
                ident = self.router.recv()  # routing information
                delimiter = self.router.recv()  # delimiter
                message = self.router.recv_json()
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

                self.router.send(ident, zmq.SNDMORE)
                self.router.send(delimiter, zmq.SNDMORE)
                self.router.send_json(reply_dict)

    def request_jam2(self):
        print("Requesting jam at {}".format(datetime.datetime.now().isoformat()))
        for ip, port in self.settings.get_ips_ports():
            msg_dict = {"jam": 0}
            ip_port = '{}:{}'.format(ip, port)
            deal_msg = self.request(ip_port, msg_dict)

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

    def request_jam(self):
        print("Requesting jam at {}".format(datetime.datetime.now().isoformat()))
        for dealer in self.dealers:
            msg_dict = {"jam": 0}
            deal_msg = self.request(dealer, msg_dict)

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

    def set_up_dealers(self):
        self.dealers.clear()

        for ip, port in self.settings.get_ips_ports():
            dealer = self.context.socket(zmq.DEALER)
            dealer.setsockopt(zmq.LINGER, 0)
            dealer.setsockopt_string(zmq.IDENTITY, "{}:{}".format(ip, port))
            dealer.connect("tcp://{}:{}".format(ip, port))
            self.dealers[ip] = dealer


if __name__ == '__main__':
    pass
    # NetworkManager()
