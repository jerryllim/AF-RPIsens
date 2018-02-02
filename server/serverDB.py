import json
import zmq
import logging
import sqlite3
import datetime
from collections import OrderedDict
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class ServerSettings:
    MACHINE_PORTS = 'machine_ports'
    QUICK_ACCESS = 'quick_access'
    SHIFT_SETTINGS = 'shift_settings'
    MISC_SETTINGS = 'misc_settings'

    def __init__(self, filename='server_settings.json'):
        self.filename = filename
        self.logger = logging.getLogger('afRPIsens_server')
        self.machine_ports = OrderedDict()
        self.quick_access = OrderedDict()
        self.shift_settings = {'Morning': ('08:00', 43200), 'Night': ('20:00', 43200)}
        self.misc_settings = {}
        self.load_settings()
        self.logger.debug('Completed setup')

    def save_settings(self):
        self.logger.debug('Saving settings')
        settings_dict = {ServerSettings.MACHINE_PORTS: self.machine_ports,
                         ServerSettings.QUICK_ACCESS: self.quick_access,
                         ServerSettings.SHIFT_SETTINGS: self.shift_settings,
                         ServerSettings.MISC_SETTINGS: self.misc_settings}
        with open(self.filename, 'w') as outfile:
            json.dump(settings_dict, outfile)
        self.logger.debug('Saved settings')

    def load_settings(self):
        self.logger.debug('Loading settings')
        try:
            with open(self.filename, 'r') as infile:
                settings_dict = json.load(infile, object_pairs_hook=OrderedDict)
                self.machine_ports = settings_dict[ServerSettings.MACHINE_PORTS]
                self.quick_access = settings_dict[ServerSettings.QUICK_ACCESS]
                self.shift_settings = settings_dict.get(ServerSettings.SHIFT_SETTINGS, self.shift_settings)
                self.misc_settings = settings_dict.get(ServerSettings.MISC_SETTINGS, self.misc_settings)
        except FileNotFoundError:
            pass
        self.logger.debug('Loaded settings')


class DatabaseManager:
    def __init__(self, database_name='afRPIsens.sqlite'):
        self.database_name = database_name

    @staticmethod
    def create_table(table_name, database):
        db = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
        try:
            db.execute("DROP TABLE IF EXISTS {}".format(table_name))
            db.execute("CREATE TABLE IF NOT EXISTS {} (time TIMESTAMP PRIMARY KEY NOT NULL, quantity INTEGER NOT NULL)"
                       .format(table_name))
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def insert_into_table(table_name, timestamp, quantity, database):
        # Establish connection and create table if not exists
        db = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
        db.execute("CREATE TABLE IF NOT EXISTS {} (time TIMESTAMP PRIMARY KEY NOT NULL, quantity INTEGER NOT NULL)"
                   .format(table_name))
        # Check if exist same timestamp for machine
        cursor = db.cursor()
        cursor.execute("SELECT * from {} WHERE time=datetime(?)", (timestamp,))
        query = cursor.fetchone()
        if query:  # TODO to test
            _timestamp, count = query
            quantity = quantity + count
            cursor.execute("UPDATE {} SET quantity = ? WHERE time = ?", (quantity, timestamp))
        else:
            cursor.execute("INSERT INTO {} VALUES(datetime(?), ?".format(table_name), (timestamp, quantity))
        db.commit()
        db.close()

    @staticmethod
    def sum_from_table(table_name, from_timestamp, to_timestamp, database, option='include'):
        db = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = db.cursor()
        if option == 'exclude':
            cursor.execute("SELECT SUM(quantity) from {} WHERE time >= datetime(?) AND time < "
                           "datetime(?)".format(table_name), (from_timestamp, to_timestamp))
        else:
            cursor.execute("SELECT SUM(quantity) from {} WHERE time >= datetime(?) AND time <= "
                           "datetime(?)".format(table_name), (from_timestamp, to_timestamp))
        summation = cursor.fetchone()[0]
        return summation

    @staticmethod
    def get_sums(machine, start, end, mode):
        """
        Returns lists from database, Hourly and Minutely is 'end' exclusive but Daily is 'end' inclusive.
        :param machine:
        :param start:
        :param end:
        :param mode:
        :return: date_list, count_list
        """
        date_list = []
        count_list = []
        check_date = start

        if mode == 'Daily':
            time_diff = datetime.timedelta(days=1)
            next_date = start.replace(minute=0, second=0, microsecond=0) + time_diff
            end = end + time_diff  # So that the end date is inclusive
        elif mode == 'Hourly':
            time_diff = datetime.timedelta(hours=1)
            next_date = start.replace(minute=0, second=0, microsecond=0) + time_diff
        else:
            time_diff = datetime.timedelta(minutes=5)
            next_date = start + time_diff

        while next_date < end:  # Loop till next_date is larger than or equal to end_date
            database = check_date.strftime('%m_%B_%Y.sqlite')
            summation = DatabaseManager.sum_from_table(machine, check_date.strftime('%Y-%m-%d %H:%M'),
                                                       next_date.strftime('%Y-%m-%d %H:%M'), database, option='exclude')
            date_list.append(check_date)
            count_list.append(summation)
            check_date = next_date
            next_date = next_date + time_diff
        # Check for the last time for between check_date and end_date
        database = check_date.strftime('%m_%B_%Y.sqlite')
        summation = DatabaseManager.sum_from_table(machine, check_date.strftime('%Y-%m-%d %H:%M'),
                                                   end.strftime('%Y-%m-%d %H:%M'), database, option='exclude')
        date_list.append(check_date)
        count_list.append(summation)

        return date_list, count_list


class Communication:
    REQUEST_ID = 'request'

    def __init__(self, server_settings: ServerSettings, database: DatabaseManager):
        self.logger = logging.getLogger('afRPIsens_server')
        self.server_settings = server_settings
        self.database = database
        self.scheduler = BackgroundScheduler()
        self.ports = []
        self.context = None
        self.socket = None

    def req_client(self):

        self.ports = list(self.server_settings.machine_ports.values())

        self.context = zmq.Context()
        self.logger.debug("Connecting to the ports")
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)
        for port in self.ports:
            self.socket.connect("tcp://{}".format(port))
            self.logger.debug("Successfully connected to machine at {}".format(port))

        for index in range(len(self.ports)):
            print("Sending request ", index, "...")
            self.socket.send_string("", zmq.SNDMORE)  # delimiter
            self.socket.send_string("Sensor Data")  # actual message

            # use poll for timeouts:
            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLIN)

            socks = dict(poller.poll(5 * 1000))
            port = self.ports[index]
            # get machine name for port
            for machine, _port in self.server_settings.machine_ports.items():
                if _port == port:
                    break

            if self.socket in socks:
                try:
                    self.socket.recv()  # discard delimiter
                    msg_json = self.socket.recv()  # actual message
                    sens = json.loads(msg_json)
                    for uniq_id, values in sens.items():
                        for timestamp, count in values.items():
                            table_name = ""'{}-{}'"".format(port, uniq_id)
                            database_name = datetime.date.today().strftime('%m_%B_%Y.sqlite')
                            self.database.insert_into_table(table_name, timestamp, count, database_name)
                except IOError:
                    self.logger.warning('Could not connect to machine {}, {}'.format(machine, port))
            else:
                self.logger.warning('Machine did not respond, ({}:{})'.format(machine, port))

        # TODO update the treeview

    def set_jobs(self):
        self.scheduler.remove_all_jobs()
        cron_trigger = CronTrigger(hour='*', minute='*/15')  # TODO set here
        self.scheduler.add_job(self.req_client, cron_trigger, id=Communication.REQUEST_ID)
