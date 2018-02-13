import json
import logging
import sqlite3
import datetime
import os
from collections import OrderedDict


class ServerSettings:
    MACHINE_PORTS = 'machine_ports'
    QUICK_ACCESS = 'quick_access'
    SHIFT_SETTINGS = 'shift_settings'
    TARGET_SETTINGS = 'target_settings'
    TARGET_MINUTES_1 = 'target_1'
    TARGET_MINUTES_2 = 'target_2'
    MACHINE_TARGETS = 'machine_targets'
    MISC_SETTINGS = 'misc_settings'
    REQUEST_TIME = 'request_time'
    FILE_PATH = 'file_path'

    def __init__(self, filename='server_settings.json'):
        self.filename = filename
        self.logger = logging.getLogger('afRPIsens_server')
        self.machine_ports = OrderedDict()
        self.quick_access = OrderedDict()
        # 43200 is 12 hours in seconds
        self.shift_settings = {'Morning': ('08:00', 43200), 'Night': ('20:00', 43200)}
        self.target_settings = {self.TARGET_MINUTES_1: ('Not set', 0, '#FFFF00'),
                                self.TARGET_MINUTES_2: ('Not set', 0, '#FFFF00'),
                                self.MACHINE_TARGETS: {}}
        self.misc_settings = {self.REQUEST_TIME: 15, self.FILE_PATH: os.path.expanduser('~/Documents')}
        self.load_settings()
        self.logger.debug('Completed setup')

    def save_settings(self):
        self.logger.debug('Saving settings')
        settings_dict = {ServerSettings.MACHINE_PORTS: self.machine_ports,
                         ServerSettings.QUICK_ACCESS: self.quick_access,
                         ServerSettings.SHIFT_SETTINGS: self.shift_settings,
                         ServerSettings.TARGET_SETTINGS: self.target_settings,
                         ServerSettings.MISC_SETTINGS: self.misc_settings}
        with open(self.filename, 'w') as outfile:
            json.dump(settings_dict, outfile)
        self.logger.debug('Saved settings')

    def load_settings(self):
        self.logger.debug('Loading settings')
        try:
            with open(self.filename, 'r') as infile:
                settings_dict = json.load(infile, object_pairs_hook=OrderedDict)
                self.machine_ports = settings_dict.get(ServerSettings.MACHINE_PORTS, self.machine_ports)
                self.quick_access = settings_dict.get(ServerSettings.QUICK_ACCESS, self.quick_access)
                self.shift_settings = settings_dict.get(ServerSettings.SHIFT_SETTINGS, self.shift_settings)
                temp_dict = self.target_settings
                self.target_settings = settings_dict.get(ServerSettings.TARGET_SETTINGS, temp_dict)
                self.target_settings[self.TARGET_MINUTES_1] = self.target_settings.get(self.TARGET_MINUTES_1,
                                                                                       temp_dict[self.TARGET_MINUTES_1])
                self.target_settings[self.TARGET_MINUTES_2] = self.target_settings.get(self.TARGET_MINUTES_2,
                                                                                       temp_dict[self.TARGET_MINUTES_2])
                self.target_settings[self.MACHINE_TARGETS] = self.target_settings.get(self.MACHINE_TARGETS,
                                                                                      temp_dict[self.MACHINE_TARGETS])
                temp_dict = self.misc_settings
                self.misc_settings = settings_dict.get(ServerSettings.MISC_SETTINGS, self.misc_settings)
                self.misc_settings[self.REQUEST_TIME] = self.misc_settings.get(self.REQUEST_TIME,
                                                                               temp_dict[self.REQUEST_TIME])
                self.misc_settings[self.FILE_PATH] = self.misc_settings.get(self.FILE_PATH,
                                                                            temp_dict[self.FILE_PATH])
        except FileNotFoundError:
            pass
        self.logger.debug('Loaded settings')

    @staticmethod
    def convert_to_duration(start, end):
        start_time = datetime.datetime.strptime(start, '%H:%M')
        end_time = datetime.datetime.strptime(end, '%H:%M')
        time_diff = end_time - start_time
        if time_diff.days < 0:
            time_diff = time_diff + datetime.timedelta(days=1)

        return time_diff

    @staticmethod
    def get_end_time(start_date, duration):
        return start_date + datetime.timedelta(seconds=duration)


class DatabaseManager:
    def __init__(self, save: ServerSettings):
        self.save = save
        self.path = self.save.misc_settings[self.save.FILE_PATH]

    def get_table_names(self, database):
        full_path = os.path.join(self.path, database)
        db = sqlite3.connect(full_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = []
        for table in cursor.fetchall():
            tables.append(table[0])

        return tables

    def create_table(self, table_name, database):
        full_path = os.path.join(self.path, database)
        db = sqlite3.connect(full_path, detect_types=sqlite3.PARSE_DECLTYPES)
        try:
            db.execute("DROP TABLE IF EXISTS {}".format(table_name))
            db.execute("CREATE TABLE IF NOT EXISTS {} (time TIMESTAMP PRIMARY KEY NOT NULL, quantity INTEGER NOT NULL)"
                       .format(table_name))
        except Exception:
            db.rollback()
        finally:
            db.close()

    def insert_into_table(self, table_name, timestamp, quantity, database):
        print(quantity)
        full_path = os.path.join(self.path, database)
        # Establish connection and create table if not exists
        db = sqlite3.connect(full_path, detect_types=sqlite3.PARSE_DECLTYPES)
        db.execute("CREATE TABLE IF NOT EXISTS {} (time TIMESTAMP PRIMARY KEY NOT NULL, quantity INTEGER NOT NULL)".format(table_name))
        # Check if exist same timestamp for machine
        cursor = db.cursor()
        cursor.execute("SELECT * from {} WHERE time=datetime(?)".format(table_name), (timestamp,))
        query = cursor.fetchone()
        print(query)
        print(table_name)
        if query:
            _timestamp, count = query
            print('Original: \t', count, '\t', quantity)
            quantity = quantity + count
            print(quantity)
            cursor.execute("UPDATE {} SET quantity = ? WHERE time = ?".format(table_name), (quantity, timestamp))
        else:
            cursor.execute("INSERT INTO {} VALUES(datetime(?), ?)".format(table_name), (timestamp, quantity))
        db.commit()
        db.close()

    def insert_to_database(self, table_name, timestamp, quantity):
        date = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
        database_name = date.strftime('%m_%B_%Y.sqlite')
        self.insert_into_table(table_name, timestamp, quantity, database_name)

    def sum_from_table(self, table_name, from_timestamp, to_timestamp, database, option='include'):
        full_path = os.path.join(self.path, database)
        db = sqlite3.connect(full_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = db.cursor()
        try:
            if option == 'exclude':
                cursor.execute("SELECT SUM(quantity) from '{}' WHERE time >= datetime(?) AND time < "
                               "datetime(?)".format(table_name), (from_timestamp, to_timestamp))
            else:
                cursor.execute("SELECT SUM(quantity) from '{}' WHERE time >= datetime(?) AND time <= "
                               "datetime(?)".format(table_name), (from_timestamp, to_timestamp))
            summation = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            summation = 0
        if summation is None:
            summation = 0

        return summation

    def get_sums(self, machine, start, end, mode):
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
            summation = self.sum_from_table(machine, check_date.strftime('%Y-%m-%d %H:%M'),
                                            next_date.strftime('%Y-%m-%d %H:%M'), database, option='exclude')
            date_list.append(check_date)
            count_list.append(summation)
            check_date = next_date
            next_date = next_date + time_diff
        # Check for the last time for between check_date and end_date
        database = check_date.strftime('%m_%B_%Y.sqlite')
        summation = self.sum_from_table(machine, check_date.strftime('%Y-%m-%d %H:%M'),
                                        end.strftime('%Y-%m-%d %H:%M'), database, option='exclude')
        date_list.append(check_date)
        count_list.append(summation)

        return date_list, count_list
