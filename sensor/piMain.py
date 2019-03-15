import os
import zmq
import time
import json
import pigpio
import sqlite3
import datetime
import threading
from collections import Counter
from apscheduler.schedulers.background import BackgroundScheduler


class PiController:
    bounce = 30
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
            output_pin = int(output_string[-2:])
            self.set_output_callback(output_pin)

        self.update_ip_ports()

        self.context = zmq.Context()
        self.respondent_routine()
        self.dealer_routine()
        self.scheduler.start()

        self.respondent_kill = threading.Event()
        self.respondent_thread = threading.Thread(target=self.respond)
        self.respondent_thread.daemon = True
        self.respondent_thread.start()

    def update_ip_ports(self):
        self.server_add = self.gui.config.get('Network', 'server_add')
        self.server_port = self.gui.config.get('Network', 'server_port')
        self.self_add = self.gui.config.get('Network', 'self_add')
        self.self_port = self.gui.config.get('Network', 'self_port')

    def load_pin_dict(self):
        try:
            with open(self.filename, 'r') as infile:
                temp = json.load(infile)
                self.pulse_pins = temp["pins"]
                self.pin_to_name = self.lookup_pin_name()
        except FileNotFoundError:
            print("File not found, ", self.filename)
            raise SystemExit

    def lookup_pin_name(self):
        temp = {}
        for name, pin in self.pulse_pins.items():
            temp[pin] = name

        return temp

    def get_key(self, idx, interval=1, emp=None):
        now = datetime.datetime.now()
        now = now - datetime.timedelta(minutes=now.minute % interval)

        if not emp:
            emp = self.gui.machines[idx].get_emp()

        jo_no = self.gui.machines[idx].get_jo_no()

        return now.strftime('%H%M'), '{0}_{1}'.format(emp, jo_no)

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

    def pin_triggered(self, pin, _level, _tick):
        name = self.pin_to_name.get(pin, None)
        if name:
            idx = int(name[-1:])
            time_, key = self.get_key(idx)
            self.update_count(time_, key, name)

    def output_pin_triggered(self, pin, _level, _tick):
        name = self.pin_to_name.get(pin, None)
        if name:
            idx = int(name[-1:])
            self.gui.update_output(idx)

    def set_output_callback(self, pin):
        self.pi.callback(pin, pigpio.RISING_EDGE, self.output_pin_triggered)

    def pin_setup(self, pin, bounce=30):
        self.pi.set_mode(pin, pigpio.INPUT)
        self.pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
        self.pi.set_glitch_filter(pin, (bounce * 1000))
        self.callbacks.append(self.pi.callback(pin, pigpio.RISING_EDGE, self.pin_triggered))

    def update_count(self, time_, key, name):
        with self.counts_lock:
            if self.counts.get(time_) is None:
                self.counts[time_] = {key: Counter()}
            elif self.counts[time_].get(key) is None:
                self.counts[time_][key] = Counter()

            self.counts[time_][key].update([name])

    def get_counts(self):
        with self.counts_lock:
            temp = self.counts.copy()
            self.counts.clear()

        return temp

    def respondent_routine(self):
        ip_port = "{}:{}".format(self.self_add, self.self_port)

        self.respondent = self.context.socket(zmq.REP)
        self.respondent.setsockopt(zmq.LINGER, 0)
        self.respondent.bind("tcp://{}".format(ip_port))

    def respond(self):
        while not self.respondent_kill:
            # wait for next request from client
            recv_message = str(self.respondent.recv(), "utf-8")
            recv_dict = json.loads(recv_message)
            reply_dict = {'ip': self.self_add}

            for key in recv_dict.keys():
                if key == "jam":
                    reply_dict["jam"] = self.get_counts()
                elif key == "job_info":
                    job_list = recv_dict.pop(key)
                    self.database_manager.renew_jobs_table(job_list)
                elif key == "emp":
                    emp_list = recv_dict.pop(key)
                    self.update_emp_info(emp_list)

            self.respondent.send_string(json.dumps(reply_dict))

    def dealer_routine(self):
        ip_port = "{}:{}".format(self.server_add, self.server_port)
        self.dealer = self.context.socket(zmq.DEALER)
        self.dealer.connect("tcp://{}".format(ip_port))

    def request(self, msg_dict):
        timeout = 2000
        msg_dict['ip'] = self.self_add
        recv_msg = None
        # Try 3 times, each waiting for 2 seconds for reply from server
        for i in range(3):
            self.dealer.send_string("", zmq.SNDMORE)
            self.dealer.send_json(msg_dict)

            if self.dealer.poll(timeout):
                self.dealer.recv()
                recv_msg = self.dealer.recv_json()
                break

        return recv_msg

    def get_job_info(self, barcode):
        job_info = self.database_manager.get_job_info(barcode)
        if job_info is None:
            reply_msg = self.request({"job_info": barcode})
            if reply_msg:
                value = reply_msg.pop(barcode)
                if value:
                    job_info = {'jo_no': value[0], 'jo_line': value[1], 'code': value[2], 'desc': value[3],
                                'to_do': value[4], 'ran': value[5]}

        return job_info

    def update_emp_info(self, emp_list):
        self.database_manager.update_into_emp_table(emp_list)

    def get_emp_name(self, emp_id):
        return self.database_manager.get_emp_name(emp_id)

    def graceful_shutdown(self):
        self.respondent_kill.set()
        self.respondent_thread.join(timeout=3)

        with self.counts_lock:
            to_save_dict = {'counter': self.counts.copy(), 'permanent': self.permanent}

        current_job = self.gui.current_job
        if current_job:
            to_save_dict.update(current_job.get_all_info)

        with open('last_save.json', 'w') as write_file:
            json.dump(to_save_dict, write_file)

        time.sleep(1)  # TODO remove sleep?
        os.system('sudo shutdown -h now')

    def save_machines(self, filename='jam_machine.json'):
        machines_save = {}
        for key, machine in self.gui.machines.items():
            machines_save[key] = machine.self_info()

        with open(filename, 'w') as write_file:
            json.dump(machines_save, write_file)


class DatabaseManager:
    def __init__(self):
        self.database = 'test.sqlite'  # TODO to change
        self.create_emp_table()
        self.create_job_table()

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
                           "(jo_no INTEGER NOT NULL, "
                           "jo_line INTEGER NOT NULL, "
                           "code TEXT NOT NULL, "
                           "desc TEXT NOT NULL, "
                           "to_do INTEGER NOT NULL, "
                           "ran INTEGER NOT NULL, "
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
            cursor.executemany("REPLACE INTO jobs_table VALUES (?, ?, ?, ?, ?, ?);", jobs_list)
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
            cursor.execute("SELECT name FROM emp_table WHERE emp_id = ? LIMIT 1;", emp_id)
            result = cursor.fetchone()
            if result:
                result = result[0]
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
            cursor.execute("DELETE FROM jobs_table WHERE jo_no = ? AND jo_line = ?;", (jo_no, jo_line))

        finally:
            db.close()
            return job_info

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
