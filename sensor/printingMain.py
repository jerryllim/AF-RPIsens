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

        self.server_add = self.gui.config.get('Network', 'ip_add')
        self.server_port = self.gui.config.get('Network', 'port')
        self.self_add = self.gui.config.get('Network', 'self_add')
        
        self.context = zmq.Context()
        # self.publisher_routine()
        self.respondent_routine()
        self.dealer_routine()
        # self.subscriber_routine()
        self.set_check_steady_job()
        self.scheduler.start()

        self.respondent_thread = threading.Thread(target=self.respond)
        self.respondent_thread.start()
        # self.requester_thread = threading.Thread(target=self.subscribe)
        # self.requester_thread.start()

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

        return temp

    @staticmethod
    def parse_job_info(data_str):
        data_list = data_str.split(";")
        values = [ast.literal_eval(value) for value in data_list]

        return values

    def parse_emp_info(self, emp_data):
        self.database_manager.update_into_employees_table(emp_data.items())

    def parse_ink_info(self, ink_data):
        self.database_manager.replace_ink_key_tables(ink_data)
    
    def respondent_routine(self):
        # TODO add self port to settings
        port_number = "{}:1234".format(self.self_add)

        self.respondent = self.context.socket(zmq.REP)
        self.respondent.setsockopt(zmq.LINGER, 0)
        print(port_number)
        self.respondent.bind("tcp://%s" % port_number)
        # print("Successfully binded to port %s for respondent" % self.port_number)

    def respond(self):
        # routine functions begins here
        while True:
            # wait for next request from client
            recv_message = str(self.respondent.recv(), "utf-8")
            recv_dict = json.loads(recv_message)
            # print("Received request (%s)" % recv_message)
            time.sleep(1)
            reply_dict = {}

            for key in recv_dict.keys():
                if key == "jam":
                    reply_dict["jam"] = self.get_counts()
                elif key == "job_info":
                    job_str = recv_dict.pop(key)
                    job_data = self.parse_job_info(job_str)
                    self.database_manager.recreate_job_table()
                    self.database_manager.insert_into_job_table(job_data)
                elif key == "emp":
                    emp_data = recv_dict.pop(key)
                    self.parse_emp_info(emp_data)
                elif key == "ink_key":
                    ink_data = recv_dict.pop(key)
                    self.parse_ink_info(ink_data)

            self.respondent.send_string(json.dumps(reply_dict))
    
    # def publisher_routine(self):
    #     # port connection sould be declared beforehand
    #     port = '{}:{}'.format(self.server_add, self.subscribe_port)
    #
    #     # establish publisher pattern and connection to server port
    #     self.publisher = self.context.socket(zmq.PUB)
    #     self.publisher.connect("tcp://%s" % port)
    #     time.sleep(1)  # Wait for publisher to connect to port
    #     # print("Successfully connected to machine %s" % port)
    #
    # def publish(self, msg):
    #     # routine function starts here
    #     msg_json = msg
    #     if self.publisher is None:
    #         self.publisher_routine()
    #
    #     self.publisher.send_string(msg_json)
        
    def dealer_routine(self):
        port_number = "{}:{}".format(self.server_add, self.server_port)
        # print("Connecting to machine...")
        self.dealer = self.context.socket(zmq.DEALER)
        self.dealer.connect("tcp://%s" % port_number)
        # print("Successfully connected to machine %s" % port_number)

    def request(self, msg_dict):
        timeout = 2000
        recv_msg = None
        # Try 3 times, each waiting for 2 seconds for reply from server
        for i in range(3):
            self.dealer.send_string("", zmq.SNDMORE)
            self.dealer.send_json(msg_dict)
            print('Attempt ', i, 'for ', msg_dict)

            if self.dealer.poll(timeout):
                self.dealer.recv()
                recv_msg = self.dealer.recv_json()
                break

        return recv_msg

    # def subscriber_routine(self):
    #     port = "152.228.1.135:56788" # TODO port add here
    #     self.subscriber = self.context.socket(zmq.SUB)
    #     self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
    #
    #     # print("Connecting to machine...")
    #     self.subscriber.bind("tcp://%s" % port)
    #     # print("Successfully connected to machine %s" % port)
    #
    # def subscribe(self):
    #     while True:
    #         # wait for messages from publishers
    #         print("Waiting for progression updates...")
    #         rev_msg = str(self.subscriber.recv())
    #         # print("Received message: %s" % rev_msg)
    #         received_json = json.loads(rev_msg)
    #         # TODO what to do with the received json
    
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
                job_info = {'jo_no': value[0], 'jo_line': value[1], 'code': value[2], 'desc': value[3], 'to_do': value[4],
                            'ran': value[5]}

        return job_info

    def get_ink_key(self, item):
        return self.database_manager.get_ink_key(item)

    def get_employee_name(self, emp_id):
        return self.database_manager.get_employee_name(emp_id)

    def replace_ink_key_tables(self, ink_key):
        self.database_manager.replace_ink_key_tables(ink_key)


class DatabaseManager:
    def __init__(self):
        self.database = 'test.sqlite'  # TODO set database name
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
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
            cursor.close()

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

    def recreate_ink_key_table(self):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS ink_key_table;")
            cursor.execute("DROP TABLE IF EXISTS ink_impression_table;")
            cursor.execute("CREATE TABLE IF NOT EXISTS ink_key_table "
                           "(item TEXT NOT NULL, "
                           "plate TEXT NOT NULL, "
                           "'1' INTEGER DEFAULT 0, "
                           "'2' INTEGER DEFAULT 0, "
                           "'3' INTEGER DEFAULT 0, "
                           "'4' INTEGER DEFAULT 0, "
                           "'5' INTEGER DEFAULT 0, "
                           "'6' INTEGER DEFAULT 0, "
                           "'7' INTEGER DEFAULT 0, "
                           "'8' INTEGER DEFAULT 0, "
                           "'9' INTEGER DEFAULT 0, "
                           "'10' INTEGER DEFAULT 0, "
                           "'11' INTEGER DEFAULT 0, "
                           "'12' INTEGER DEFAULT 0, "
                           "'13' INTEGER DEFAULT 0, "
                           "'14' INTEGER DEFAULT 0, "
                           "'15' INTEGER DEFAULT 0, "
                           "'16' INTEGER DEFAULT 0, "
                           "'17' INTEGER DEFAULT 0, "
                           "'18' INTEGER DEFAULT 0, "
                           "'19' INTEGER DEFAULT 0, "
                           "'20' INTEGER DEFAULT 0, "
                           "'21' INTEGER DEFAULT 0, "
                           "'22' INTEGER DEFAULT 0, "
                           "'23' INTEGER DEFAULT 0, "
                           "'24' INTEGER DEFAULT 0, "
                           "'25' INTEGER DEFAULT 0, "
                           "'26' INTEGER DEFAULT 0, "
                           "'27' INTEGER DEFAULT 0, "
                           "'28' INTEGER DEFAULT 0, "
                           "'29' INTEGER DEFAULT 0, "
                           "'30' INTEGER DEFAULT 0, "
                           "'31' INTEGER DEFAULT 0, "
                           "'32' INTEGER DEFAULT 0, "
                           "PRIMARY KEY(item, plate));")
            cursor.execute("CREATE TABLE IF NOT EXISTS ink_impression_table (item TEXT PRIMARY KEY, impression INTEGER "
                           "NOT NULL);")
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

    def replace_ink_key_tables(self, ink_key):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        for item, info in ink_key.items():
            impression = info.pop('impression')
            cursor.execute("REPLACE INTO ink_impression_table VALUES (?, ?)", (item, impression))
            for plate, i_keys in info.items():
                keys = ",".join("'{}'".format(k) for k in range(1, len(i_keys)+1))
                qm = ",".join(list('?'*len(i_keys)))
                values = [item, plate] + i_keys
                cursor.execute("REPLACE INTO ink_key_table (item,plate," + keys + ") VALUES (?,?," + qm + ");", values)

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

        cursor.execute("DELETE FROM job_info_table WHERE jo_no = ? AND jo_line = ? LIMIT 1;", (jo_no, jo_line))

        db.close()

        return job_info

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_ink_key(self, item):
        """Returns empty dictionary if not found"""
        db = sqlite3.connect(self.database)
        # db.row_factory = self.dict_factory
        cursor = db.cursor()

        d = {}

        cursor.execute("SELECT impression FROM ink_impression_table WHERE item = ?;", (item, ))
        impression_d = cursor.fetchone()
        if impression_d:
            d['impression'] = impression_d[0]

        cursor.execute("SELECT plate, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`,"
                       " `9`, `10`, `11`, `12`, `13`, `14`, `15`, `16`,"
                       " `17`, `18`, `19`, `20`, `21`, `22`, `23`, `24`,"
                       " `25`, `26`, `27`, `28`, `29`, `30`, `31`, `32`"
                       " FROM ink_key_table WHERE item = ?", (item, ))

        for row in cursor:
            # plate = row.pop('plate')
            # row.pop('item')
            # new = {k: v for k, v in row.items() if v is not None}
            list_row = list(row)
            plate = list_row.pop(0)

            d[plate] = list_row

        db.close()

        return d
