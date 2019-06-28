import os
import csv
import zmq
import time
import json
import pigpio
import logging
import sqlite3
import datetime
import threading
from io import StringIO
from collections import Counter
from apscheduler.schedulers.background import BackgroundScheduler


class PiController:
    # Pipe variables
    MAX_MISSED = 3  # Max missed pings
    PING_INTERVAL = 5  # minutes
    pipe_add = "inproc://pipe1"
    ping_at = 0
    last_ping = 0
    pipe_a = None
    pipe_b = None

    TIMEOUT = 1000
    pulse_pins = {}
    pin_to_name = {}
    counts = {}
    permanent = 0
    publisher = None
    respondent = None
    dealer = None
    subscriber = None
    server_add = None
    server_port = None
    self_add = None
    self_port = None

    def __init__(self, gui, filename='pin_dict.json'):
        # Logger setup
        self.logger = logging.getLogger('JAM')
        self.logger.setLevel(logging.DEBUG)
        now = datetime.datetime.now()
        log_file = '/home/pi/jam_logs/jam{}.log'.format(now.strftime('%y%m%d_%H%M'))
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        log_format = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s: %(module)s - %(message)s')
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)
        self.logger.info('Started logging')

        self.filename = filename
        self.callbacks = []
        self.counts_lock = threading.Lock()
        self.scheduler = BackgroundScheduler()
        self.gui = gui
        self.database_manager = DatabaseManager()
        self.load_pin_dict()
        self.pi = pigpio.pi()

        # TODO request job_info?

        for name, pin in self.pulse_pins.items():
            self.pin_setup(pin)

        for idx in range(1, 4):
            output_string = self.gui.config.get('General{}'.format(idx), 'output_pin')
            output_pin = self.pulse_pins['{}{}'.format(output_string, idx)]
            self.set_output_callback(output_pin)

        self.update_ip_ports()

        self.context = zmq.Context()
        self.respondent_routine()
        self.dealer_routine()
        self.pipe_routine()
        self.ping_at = time.time() + 60*self.PING_INTERVAL
        self.scheduler.start()

        self.respondent_kill = threading.Event()
        self.respondent_thread = threading.Thread(target=self.respond)
        self.respondent_thread.daemon = True
        self.respondent_thread.start()
        self.pipe_thread = threading.Thread(target=self.pipe_loop)
        self.pipe_thread.daemon = True
        self.pipe_thread.start()
        self.logger.info('Completed PiController __init__')

    def update_ip_ports(self):
        self.server_add = self.gui.config.get('Network', 'server_add')
        self.server_port = self.gui.config.get('Network', 'server_port')
        self.self_add = self.gui.config.get('Network', 'self_add')
        self.self_port = self.gui.config.get('Network', 'self_port')
        self.logger.info('Updating ports')

    def load_pin_dict(self):
        try:
            with open(self.filename, 'r') as infile:
                temp = json.load(infile)
                self.pulse_pins = temp["pins"]
                self.pin_to_name = self.lookup_pin_name()
        except FileNotFoundError:
            self.logger.error("File not found, ", self.filename)
            raise SystemExit

    def lookup_pin_name(self):
        temp = {}
        for name, pin in self.pulse_pins.items():
            temp[pin] = name

        return temp

    def get_key(self, idx, interval=1, emp=None):
        now = datetime.datetime.now()
        # Floor to nearest interval (default = 5)
        now = now - datetime.timedelta(minutes=now.minute % interval)

        try:
            if not emp:
                emp = self.gui.machines[idx].get_emp()

            jo_no = self.gui.machines[idx].get_jo_no()

        except KeyError as error:
            self.logger.warning("Key error in get_key: {}".format(error))
            emp = None
            jo_no = ''

        return '{0}_{1}_{2}'.format(emp, jo_no, now.strftime('%d%H%M'))

    def add_qc(self, idx, string):
        key = 'Q{}'.format(idx)
        with self.counts_lock:
            if self.counts.get(key) is None:
                self.counts[key] = []

            self.counts[key].append(string)

    def add_maintenance(self, idx, emp_start, end=None):
        key = 'M{}'.format(idx)
        with self.counts_lock:
            if self.counts.get(key) is None:
                self.counts[key] = {}

            self.counts[key][emp_start] = end

    def add_employee(self, idx, emp_start, end=None):
        key = 'E{}'.format(idx)
        with self.counts_lock:
            if self.counts.get(key) is None:
                self.counts[key] = {}

            self.counts[key][emp_start] = end

    def add_sfu(self, sfu_str):
        key = 'sfu'
        with self.counts_lock:
            if self.counts.get(key) is None:
                self.counts[key] = []

            self.counts[key].append(sfu_str)

    def publish_sfu(self, sfu_str):
        reply = self.request({'sfu': sfu_str})
        if reply is None:
            self.logger.warning('Server did not respond to sfu')
            self.add_sfu(sfu_str)

    def pin_triggered(self, pin, _level, _tick):
        name = self.pin_to_name.get(pin, None)
        if name:
            idx = int(name[-1:])
            key = self.get_key(idx)
            self.update_count(key, name)

    def output_pin_triggered(self, pin, _level, _tick):
        name = self.pin_to_name.get(pin, None)
        if name:
            idx = int(name[-1:])
            self.gui.update_output(idx)

    def set_output_callback(self, pin):
        self.pi.callback(pin, pigpio.RISING_EDGE, self.output_pin_triggered)

    def pin_setup(self, pin, steady=500):
        self.pi.set_mode(pin, pigpio.INPUT)
        self.pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
        self.pi.set_glitch_filter(pin, steady)
        self.callbacks.append(self.pi.callback(pin, pigpio.RISING_EDGE, self.pin_triggered))

    def update_count(self, key, name):
        with self.counts_lock:
            if self.counts.get(key) is None:
                self.counts[key] = Counter()
            self.counts[key].update([name])

    def update_adjustments(self, key, name, value):
        with self.counts_lock:
            if self.counts.get(key) is None:
                self.counts[key] = Counter()
            self.counts[key][name] = value

    def get_counts(self):
        with self.counts_lock:
            temp = self.counts.copy()
            self.counts.clear()

        return temp

    def respondent_routine(self):
        self.respondent = self.context.socket(zmq.DEALER)
        self.respondent.setsockopt(zmq.LINGER, 0)
        self.respondent.setsockopt_string(zmq.IDENTITY, self.self_add)
        self.respondent.setsockopt(zmq.IMMEDIATE, 1)
        self.respondent.setsockopt(zmq.TCP_KEEPALIVE, 1)
        self.respondent.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 1)
        self.respondent.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
        self.respondent.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
        self.respondent.bind("tcp://{}:{}".format(self.self_add, self.self_port))
        self.logger.debug('Created respondent socket for request with {}:{}'.format(self.self_add, self.self_port))

    def respond(self):
        self.logger.info("Starting respond loop")
        while not self.respondent_kill.is_set():
            if self.respondent.poll(10):
                # wait for next request from client
                recv_message = str(self.respondent.recv(), "utf-8")
                recv_dict = json.loads(recv_message)
                # reply_dict = {'ip': self.self_add}
                reply_dict = {}

                for key in recv_dict.keys():
                    if key == "jam":
                        reply_dict["jam"] = self.get_counts()
                    elif key == "jobs":
                        jobs_str = recv_dict.get(key)
                        with StringIO(jobs_str) as jobs:
                            csv_reader = csv.reader(jobs)
                            jobs_list = list(csv_reader)
                        # TODO convert string to list before replace_into_jobs_table
                        self.database_manager.replace_into_jobs_table(jobs_list)
                        reply_dict["jobs"] = 1
                    elif key == "emp":
                        emp_list = recv_dict.get(key)
                        self.update_emp_info(emp_list)

                self.respondent.send_string(json.dumps(reply_dict))
                self.logger.debug("Received {}, replying with {}".format(recv_dict, reply_dict))

    def dealer_routine(self):
        ip_port = "{}:{}".format(self.server_add, self.server_port)
        self.dealer = self.context.socket(zmq.DEALER)
        self.dealer.setsockopt_string(zmq.IDENTITY, self.self_add)
        self.dealer.setsockopt(zmq.IMMEDIATE, 1)
        self.dealer.setsockopt(zmq.TCP_KEEPALIVE, 1)
        self.dealer.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 1)
        self.dealer.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
        self.dealer.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
        self.dealer.connect("tcp://{}".format(ip_port))
        self.logger.debug('Created dealer socket for request {}'.format(ip_port))

    def request(self, msg_dict):
        # Clear buffer by restarting the dealer socket
        # self.dealer.setsockopt(zmq.LINGER, 0)
        # self.dealer.close()
        # self.dealer_routine()

        timeout = self.TIMEOUT
        # msg_dict['ip'] = self.self_add
        recv_msg = None
        # Try 3 times, each waiting for 2 seconds for reply from server
        self.logger.debug('Sending request to server')
        if "job_info" in msg_dict.keys():
            validation = msg_dict.get("job_info")
            self.logger.debug("Has validation key {}".format(str(validation)))
        else:
            validation = None

        for i in range(3):
            self.dealer.send_json(msg_dict)

            while self.dealer.poll(timeout):
                reply = json.loads(str(self.dealer.recv(), "utf-8"))
                if validation is None or validation in reply.keys():
                    self.logger.debug("{}".format(str(reply.keys())))
                    recv_msg = reply
                    self.logger.debug('Received reply {} from server on try {}'.format(recv_msg, i))
                    return recv_msg

            if recv_msg is None:
                self.logger.debug('No response from server on try {}. Closing dealer socket'.format(i))
                # No response from server. Close dealer socket
                self.dealer.setsockopt(zmq.LINGER, 0)
                self.dealer.close()
                # Recreate dealer socket
                self.dealer_routine()
            else:
                self.logger.debug("Breaking the loop")
                break

        return recv_msg

    def get_job_info(self, barcode):
        job_info = self.database_manager.get_job_info(barcode)
        if not job_info:
            reply_msg = self.pipe_talk({"job_info": barcode})
            # reply_msg = self.request({"job_info": barcode})
            if isinstance(reply_msg, dict):
                value = reply_msg.pop(barcode)
                if value:
                    job_info = {'jo_no': value[0], 'jo_line': value[1], 'code': value[2], 'desc': value[3],
                                'to_do': value[4], 'ran': value[5]}
                else:
                    job_info = {}
        else:
            self.logger.debug("Found {} in database".format(barcode))

        return job_info

    def pipe_routine(self):
        self.pipe_a = self.context.socket(zmq.PAIR)
        self.pipe_a.setsockopt(zmq.LINGER, 0)
        self.pipe_a.set_hwm(1)
        self.pipe_a.bind(self.pipe_add)

        self.pipe_b = self.context.socket(zmq.PAIR)
        self.pipe_b.setsockopt(zmq.LINGER, 0)
        self.pipe_b.set_hwm(1)
        self.pipe_b.connect(self.pipe_add)
        self.logger.debug('Created pipe sockets')

    def pipe_talk(self, msg_dict):
        timeout = self.TIMEOUT*3 + 100
        self.pipe_b.send_json(msg_dict)
        reply = 0

        if self.pipe_b.poll(timeout):
            reply = self.pipe_b.recv_json()

        return reply

    def pipe_loop(self):
        while True:
            timeout = self.ping_at - time.time()
            if self.pipe_a.poll(1000*timeout):
                msg_dict = self.pipe_a.recv_json()
                self.logger.debug("Preparing to send message {}".format(msg_dict))

                reply = self.request(msg_dict)
                # Update ping if successful replied
                if reply is not None:
                    self.ping_at = time.time() + 60*self.PING_INTERVAL

                self.pipe_a.send_json(reply)

            # To check if need to ping
            self.ping()

    def ping(self):
        if time.time() > self.ping_at:
            reply = self.request({"ping": 0})
            if reply and reply.pop("pong", None):
                self.last_ping = time.time()
                self.logger.debug("Server replied ping")
            else:
                self.logger.debug("Server did not reply pong")

            self.ping_at = time.time() + 60*self.PING_INTERVAL

    def update_emp_info(self, emp_list):
        self.database_manager.update_into_emp_table(emp_list)

    def get_emp_name(self, emp_id):
        return self.database_manager.get_emp_name(emp_id)

    def graceful_shutdown(self):
        self.respondent_kill.set()
        self.respondent_thread.join(timeout=3)
        # TODO close all sockets

        with self.counts_lock:
            to_save_dict = {'counter': self.counts.copy(), 'permanent': self.permanent}

        current_job = self.gui.current_job
        if current_job:
            to_save_dict.update(current_job.get_all_info)

        with open('last_save.json', 'w') as write_file:
            json.dump(to_save_dict, write_file)

        time.sleep(1)  # TODO remove sleep?
        os.system('sudo shutdown -h now')

    def save_pi(self, filename='jam_machine.json'):
        self.logger.info("Saving machines")
        save_dict = {'save_time': datetime.datetime.now()}
        with self.counts_lock:
            save_dict['counts'] = self.counts.copy()

        for key, machine in self.gui.machines.items():
            save_dict[key] = machine.all_info()

        with open(filename, 'w') as write_file:
            json.dump(save_dict, write_file, default=str)


class DatabaseManager:
    def __init__(self):
        self.logger = logging.getLogger('JAM')

        self.database = 'jam.sqlite'  # TODO to change
        # self.create_emp_table()
        self.create_job_table()
        self.logger.info('Completed DatabaseManager __init__')

    def create_emp_table(self):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute("CREATE TABLE IF NOT EXISTS emp_table (emp_id TEXT PRIMARY KEY, name TEXT);")
            db.commit()
        finally:
            db.close()

    def create_job_table(self):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute("CREATE TABLE IF NOT EXISTS jobs_table "
                           "(jo_no TEXT NOT NULL, "
                           "jo_line INTEGER NOT NULL, "
                           "code TEXT NOT NULL, "
                           "desc TEXT NOT NULL, "
                           "to_do INTEGER NOT NULL, "
                           "ran INTEGER NOT NULL, "
                           "ludt TEXT NOT NULL, "
                           "PRIMARY KEY(jo_no, jo_line));")
            db.commit()
        finally:
            db.close()

    def replace_into_emp_table(self, emp_list):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.executemany("REPLACE INTO emp_table VALUES (?, ?);", emp_list)
            db.commit()
        finally:
            db.close()

    def replace_into_jobs_table(self, jobs_list):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.executemany("REPLACE INTO jobs_table VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'));", jobs_list)
            db.commit()
        finally:
            db.close()

    def delete_old_jobs(self):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute("DELETE FROM jobs_table WHERE ludt <= datetime('now', 'locatime', '-7 days';")
            db.commit()
        finally:
            db.close()

    def renew_jobs_table(self, jobs_list):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute("DROP IF EXISTS jobs_table;")
            db.commit()
        finally:
            db.close()

        self.create_job_table()
        self.replace_into_jobs_table(jobs_list)

    def update_into_emp_table(self, emp_list):
        self.replace_into_emp_table(emp_list)
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute("DELETE FROM emp_table WHERE name IS NULL;")
            db.commit()
        finally:
            db.close()

    def get_emp_name(self, emp_id):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        result = ''
        try:
            cursor.execute("SELECT name FROM emp_table WHERE emp_id = ? LIMIT 1;", (emp_id,))
            row = cursor.fetchone()
            if row:
                result = row[0]
            else:
                result = emp_id
        finally:
            db.close()
            return result

    def get_job_info(self, barcode):
        jo_no = barcode[:-3]
        jo_line = int(barcode[-3:])
        db = sqlite3.connect(self.database)
        db.row_factory = self.dict_factory
        cursor = db.cursor()
        job_info = {}

        try:
            cursor.execute("SELECT * FROM jobs_table WHERE jo_no = ? AND jo_line = ? LIMIT 1;", (jo_no, jo_line))
            job_info = cursor.fetchone()
            cursor.execute("DELETE FROM jobs_table WHERE jo_no = ? AND jo_line = ? LIMIT 1;", (jo_no, jo_line))

        finally:
            db.close()
            return job_info

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
