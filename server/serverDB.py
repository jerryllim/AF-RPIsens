import json
import logging
import sqlite3
import datetime
from collections import OrderedDict


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
        # 43200 is 12 hours in seconds
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

    @staticmethod
    def convert_to_duration(start, end):
        start_time = datetime.datetime.strptime(start, '%H:%M')
        end_time = datetime.datetime.strptime(end, '%H:%M')
        time_diff = end_time - start_time

        return time_diff

    @staticmethod
    def get_end_time(start_date, duration):
        return start_date + datetime.timedelta(seconds=duration)


class DatabaseManager:
    def __init__(self, database_name='afRPIsens.sqlite'):
        self.database_name = database_name

    @staticmethod
    def get_table_names(database):
        # TODO check if there is the file
        db = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = []
        for table in cursor.fetchall():
            tables.append(table[0])

        return tables

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
    def insert_to_database(table_name, timestamp, quantity):
        date = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
        database_name = date.strftime('%m_%B_%Y.sqlite')
        DatabaseManager.insert_into_table(table_name, timestamp, quantity, database_name)

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
