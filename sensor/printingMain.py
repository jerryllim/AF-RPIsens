import os
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
    STEADY_ID = 'steady_pin_check'
    # states = {}

    def __init__(self, gui, filename='pin_dict.json'):
        self.filename = filename
        self.callbacks = []
        self.counts_lock = threading.Lock()
        self.scheduler = BackgroundScheduler()
        self.gui = gui
        self.load_pin_dict()
        self.pi = pigpio.pi()

        for name, pin in self.pulse_pins.items():
            self.pin_setup(pin)
        for name, pin in self.steady_pins.items():
            self.pin_setup2(pin)

        output_string = self.gui.config.get('General', 'output_pin')
        output_pin = int(output_string[-2:])
        self.set_output_callback(output_pin)

        self.server_add = self.gui.config.get('Network', 'ip_add')
        self.subscribe_port = self.gui.config.get('Network', 'port')
        self.self_add = self.gui.config.get('Network', 'self_add')

        self.publisher_routine()
        self.respondent_routine()
        self.set_check_steady_job()
        self.scheduler.start()

        self.respondent_thread = threading.Thread(target=self.respond)
        self.respondent_thread.start()

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

    def get_key(self, interval=5, emp=None):
        # TODO change to UTC now?
        now = datetime.datetime.now()
        # Floor to nearest interval (default = 5)
        now = now - datetime.timedelta(minutes=now.minute % interval)

        if not emp:
            emp = self.gui.action_bar.employees[1]

        if self.gui.current_job:
            jo_no = self.gui.current_job.get_current_job()
        else:
            jo_no = 'None'

        return '{0}_{1}_{2}'.format(emp, jo_no, now.strftime('%Y%m%d%H%M'))

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

        return json.dumps(temp)
    
    def respondent_routine(self):
        port_number = "{}:9999".format(self.self_add)

        context = zmq.Context()
        self.respondent = context.socket(zmq.REP)
        self.respondent.setsockopt(zmq.LINGER, 0)
        self.respondent.bind("tcp://%s" % port_number)
        # print("Successfully binded to port %s for respondent" % self.port_number)

    def respond(self):
        # routine functions begins here
        while True:
            # wait for next request from client
            _message = str(self.respondent.recv(), "utf-8")
            # print("Received request (%s)" % _message)
            time.sleep(1)
            res_json = self.get_counts()
            self.respondent.send_string(res_json)
    
    def publisher_routine(self):
        # port connection sould be declared beforehand
        port = '{}:{}'.format(self.server_add, self.subscribe_port)

        # establishing context, publisher pattern and connection to server port
        context = zmq.Context()
        self.publisher = context.socket(zmq.PUB)
        self.publisher.connect("tcp://%s" % port)
        time.sleep(1)  # Wait for publisher to connect to port
        # print("Successfully connected to machine %s" % port)

    def publish(self, msg):
        # routine function starts here
        msg_json = msg
        if self.publisher is None:
            self.publisher_routine()

        self.publisher.send_string(msg_json)

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


class DatabaseManager:
    def __init__(self):
        self.database = 'test.sqlite'  # TODO set database name
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees';")
        if not cursor.fetchone():
            self.recreate_employees_table()

    def recreate_employees_table(self):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS employees;")
            cursor.execute("CREATE TABLE IF NOT EXISTS employees (emp_id TEXT PRIMARY KEY, name TEXT);")
            db.commit()
        finally:
            cursor.close()

    def recreate_job_table(self):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS job_info;")
            cursor.execute("CREATE TABLE IF NOT EXISTS job_info (jo_no INTEGER NOT NULL, jo_line INTEGER NOT NULL, code"
                           " TEXT NOT NULL, desc TEXT NOT NULL, to_do INTEGER NOT NULL, ran INTEGER NOT NULL, PRIMARY "
                           "KEY(jo_no, jo_line));")
            db.commit()
        finally:
            db.close()

    def recreate_ink_key_table(self):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS ink_key;")
            cursor.execute("DROP TABLE IF EXISTS ink_impression;")
            cursor.execute("CREATE TABLE IF NOT EXISTS ink_key (item TEXT NOT NULL, plate TEXT NOT NULL, '1' INTEGER, "
                           "'2' INTEGER, '3' INTEGER, '4' INTEGER, '5' INTEGER, '6' INTEGER, '7' INTEGER, '8' INTEGER, "
                           "'9' INTEGER, '10' INTEGER, '11' INTEGER, '12' INTEGER, '13' INTEGER, '14' INTEGER, '15' "
                           "INTEGER, '16' INTEGER, '17' INTEGER, '18' INTEGER, '19' INTEGER, '20' INTEGER, '21' INTEGER"
                           ", '22' INTEGER, '23' INTEGER, '24' INTEGER, '25' INTEGER, '26' INTEGER, '27' INTEGER, '28' "
                           "INTEGER, '29' INTEGER, '30' INTEGER, '31' INTEGER, '32' INTEGER, PRIMARY KEY(item, plate));")
            cursor.execute("CREATE TABLE IF NOT EXISTS ink_impression (item TEXT PRIMARY KEY, impression INTEGER NOT NULL);")
            db.commit()
        finally:
            db.close()

    def replace_into_employees_table(self, emp_list):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        cursor.executemany("REPLACE INTO employees VALUES (?, ?);", emp_list)
        db.commit()
        db.close()

    def insert_into_job_table(self, job_info):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        cursor.executemany("INSERT INTO job_info VALUES (?, ?, ?, ?, ?, ?);", job_info)
        db.commit()
        db.close()

    def update_into_employees_table(self, emp_list):
        self.replace_into_employees_table(emp_list)
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        cursor.execute("DELETE FROM employees WHERE name IS NULL;")
        db.commit()
        db.close()

    def replace_ink_key_tables(self, ink_key):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        for item, info in ink_key.items():
            impression = info.pop('impression')
            cursor.execute("REPLACE INTO ink_impression VALUES (?, ?)", (item, impression))
            for plate, zones in info.items():
                keys = ",".join("'{}'".format(k) for k in zones.keys())
                qm = ",".join(list('?'*len(zones.values())))
                values = (item, plate) + tuple(zones.values())
                cursor.execute("REPLACE INTO ink_key (item,plate," + keys + ") VALUES (?,?," + qm + ");", values)

    def get_employee_name(self, emp_id):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM employees WHERE emp_id = ?;", (emp_id, ))
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
        cursor.execute("SELECT * FROM job_info WHERE jo_no = ? AND jo_line = ?;", (jo_no, jo_line))
        # TODO request from server if not found
        return cursor.fetchone()

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_ink_key(self, item):
        """Returns empty dictionary if not found"""
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        db.row_factory = self.dict_factory

        d = {}

        cursor.execute("SELECT impression FROM ink_impression WHERE item = ?;", (item, ))
        impression_d = cursor.fetchone()
        if impression_d:
            d.update(impression_d)

        cursor.execute("SELECT * FROM ink_key WHERE item = ?", (item, ))

        for row in cursor:
            plate = row.pop('plate')
            row.pop('item')
            d[plate] = row

        return d
