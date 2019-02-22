import ast
import zmq
import time
import json
import pigpio
import sqlite3
import datetime
import threading
from collections import Counter
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler


class RaspberryPiController:
    bounce = 30
    pulse_pins = {}
    steady_pins = {}
    pin_to_name = {}
    counts = {}
    _output = 0
    publisher = None
    respondent = None
    dealer = None
    subscriber = None
    STEADY_ID = 'steady_pin_check'
    server_add = None
    server_port = None
    self_add = None
    self_port = None
    # states = {}

    def __init__(self, gui, filename='pin_dict.json'):
        self.filename = filename
        self.callbacks = []
        self.counts_lock = threading.Lock()
        self.scheduler = BackgroundScheduler()
        self.gui = gui
        self.database_manager = DatabaseManager()
        self.load_pin_dict()
        self.pi = pigpio.pi()

        for name, pin in self.pulse_pins.items():
            self.pin_setup(pin)
        for name, pin in self.steady_pins.items():
            self.pin_setup2(pin)

        output_string = self.gui.config.get('General', 'output_pin')
        output_pin = int(output_string[-2:])
        self.set_output_callback(output_pin)

        self.update_ip_ports()
        
        self.context = zmq.Context()
        self.respondent_routine()
        self.dealer_routine()
        self.set_check_steady_job()
        self.scheduler.start()

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
                self.pulse_pins = temp["pulse"]
                self.steady_pins = temp["steady"]
                self.pin_to_name = self.lookup_pin_name()
        except FileNotFoundError:
            # TODO either log or stop program since not recording pins
            print("File not found, ", self.filename)
            raise SystemExit

    def lookup_pin_name(self):
        temp = {}
        for name, pin in self.pulse_pins.items():
            temp[pin] = name

        for name, pin in self.steady_pins.items():
            temp[pin] = name

        return temp

    def get_key(self, interval=1, emp=None):
        # TODO change to UTC now?
        now = datetime.datetime.now()
        # Floor to nearest interval (default = 5)
        now = now - datetime.timedelta(minutes=now.minute % interval)

        if not emp:
            if self.gui.action_bar and self.gui.action_bar.employees.get(1):
                emp = self.gui.action_bar.employees[1]
            else:
                emp = None

        if self.gui.current_job:
            jo_no = self.gui.current_job.get_current_job()
        else:
            jo_no = 'None'

        return '{0}_{1}_{2}'.format(emp, jo_no, now.strftime('%H%M'))

    def get_key_tuple(self, interval=1, emp=None):
        # TODO change to UTC now?
        now = datetime.datetime.now()
        # Floor to nearest interval (default = 5)
        now = now - datetime.timedelta(minutes=now.minute % interval)

        if not emp:
            if self.gui.action_bar and self.gui.action_bar.employees.get(1):
                emp = self.gui.action_bar.employees[1]
            else:
                emp = None

        if self.gui.current_job:
            jo_no = self.gui.current_job.get_current_job()
        else:
            jo_no = 'None'

        return [emp, jo_no, now.strftime('%H%M')]

    def add_qc(self, emp, _pass):
        key = self.get_key_tuple(emp=emp)

        with self.counts_lock:
            if self.counts.get('qc') is None:
                self.counts['qc'] = []

            self.counts['qc'].append(key + [int(_pass)])

    def add_maintenance(self, emp, start):
        key = self.get_key_tuple(emp=emp)

        with self.counts_lock:
            if self.counts.get('maintenance') is None:
                self.counts['maintenance'] = []

            self.counts['maintenance'].append(key + [int(start)])

    def pin_triggered(self, pin, _level, _tick):
        name = self.pin_to_name[pin]
        key = self.get_key()
        self.update_count(name, key)

    def output_pin_triggered(self, _pin, _level, _tick):
        # TODO store output here? and to FeRAM?
        self._output += 1
        self.gui.update_output()

    def set_output_callback(self, pin):
        self.pi.callback(pin, pigpio.RISING_EDGE, self.output_pin_triggered)

    def pin_setup(self, pin, bounce=30):
        self.pi.set_mode(pin, pigpio.INPUT)
        self.pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
        self.pi.set_glitch_filter(pin, (bounce * 1000))
        self.callbacks.append(self.pi.callback(pin, pigpio.RISING_EDGE, self.pin_triggered))

    def pin_setup2(self, pin, bounce=30):
        self.pi.set_mode(pin, pigpio.INPUT)
        self.pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
        self.pi.set_glitch_filter(pin, (bounce * 1000))
        self.callbacks.append(self.pi.callback(pin, pigpio.EITHER_EDGE, self.pin_triggered2))
        # self.states[pin] = 0

    def update_count(self, name, key):
        with self.counts_lock:
            if self.counts.get(key) is None:
                self.counts[key] = Counter()
            self.counts[key].update([name])

    def get_counts(self):
        with self.counts_lock:
            temp = self.counts.copy()
            self.counts.clear()

        return temp

    def parse_emp_info(self, emp_data):
        self.database_manager.update_into_employees_table(emp_data.items())
    
    def respondent_routine(self):
        port_number = "{}:{}".format(self.self_add, self.self_port)

        self.respondent = self.context.socket(zmq.REP)
        self.respondent.setsockopt(zmq.LINGER, 0)
        self.respondent.bind("tcp://%s" % port_number)

    def respond(self):
        # routine functions begins here
        while True:
            # wait for next request from client
            recv_message = str(self.respondent.recv(), "utf-8")
            recv_dict = json.loads(recv_message)
            reply_dict = {'ip': self.self_add}

            for key in recv_dict.keys():
                if key == "jam":
                    reply_dict["jam"] = self.get_counts()
                elif key == "job_info":
                    job_list = recv_dict.pop(key)
                    self.database_manager.recreate_job_table()
                    self.database_manager.insert_into_job_table(job_list)
                elif key == "emp":
                    emp_data = recv_dict.pop(key)
                    self.parse_emp_info(emp_data)

            self.respondent.send_string(json.dumps(reply_dict))
        
    def dealer_routine(self):
        port_number = "{}:{}".format(self.server_add, self.server_port)
        self.dealer = self.context.socket(zmq.DEALER)
        self.dealer.connect("tcp://%s" % port_number)

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
    
    def pin_triggered2(self, pin, level, _tick):
        name = self.pin_to_name[pin]
        # self.states[name] = level
        key = self.get_key()

        if level and not self.counts[key][name]:
            self.update_count(name, key)

    def set_check_steady_job(self):
        cron_trigger = CronTrigger(minute='*/5')
        self.scheduler.add_job(self.check_pin_states, cron_trigger, id=self.STEADY_ID)
        
    def check_pin_states(self):
        for name, pin in self.steady_pins.items():
            state = self.pi.read(pin)

            if state:
                # name = self.pin_to_name[pin]
                key = self.get_key()
                self.update_count(name, key)

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

    def get_employee_name(self, emp_id):
        return self.database_manager.get_employee_name(emp_id)


class DatabaseManager:
    def __init__(self):
        self.database = 'test.sqlite'  # TODO set database name
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='job_info_table';")
        if not cursor.fetchone():
            self.recreate_job_table()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees_table';")
        if not cursor.fetchone():
            self.recreate_employees_table()

    def recreate_employees_table(self):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS employees_table;")
            cursor.execute("CREATE TABLE IF NOT EXISTS employees_table (emp_id TEXT PRIMARY KEY, name TEXT);")
            db.commit()
        finally:
            db.close()

    def recreate_job_table(self):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS job_info_table;")
            cursor.execute("CREATE TABLE IF NOT EXISTS job_info_table "
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

    def replace_into_employees_table(self, emp_list):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        cursor.executemany("REPLACE INTO employees_table VALUES (?, ?);", emp_list)
        db.commit()
        db.close()

    def insert_into_job_table(self, job_info):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        cursor.executemany("INSERT INTO job_info_table VALUES (?, ?, ?, ?, ?, ?);", job_info)
        db.commit()
        db.close()

    def update_into_employees_table(self, emp_list):
        self.replace_into_employees_table(emp_list)
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        cursor.execute("DELETE FROM employees_table WHERE name IS NULL;")
        db.commit()
        db.close()

    def get_employee_name(self, emp_id):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM employees_table WHERE emp_id = ?;", (emp_id, ))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return emp_id

    def get_job_info(self, barcode):
        jo_no = barcode[:-3]
        jo_line = int(barcode[-3:])
        db = sqlite3.connect(self.database)
        db.row_factory = self.dict_factory
        cursor = db.cursor()

        cursor.execute("SELECT * FROM job_info_table WHERE jo_no = ? AND jo_line = ? LIMIT 1;", (jo_no, jo_line))
        job_info = cursor.fetchone()

        cursor.execute("DELETE FROM job_info_table WHERE jo_no = ? AND jo_line = ?;", (jo_no, jo_line))

        db.close()

        return job_info

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
