import os
import csv
import sys
import sqlite3
import logging
import pymysql
import warnings
import configparser
from datetime import datetime, timedelta


class Settings:
    def __init__(self, filename='jam.ini'):
        self.logger = logging.getLogger('jamVIEWER')

        self.filename = filename
        self.config = configparser.ConfigParser()
        path = os.path.expanduser('~/Documents/JAM/JAMviewer/' + self.filename)
        self.config.read(path)
        self.machines_info = {}
        self.update()
        self.logger.info('Completed Settings __init__')

    def update(self):
        self.config.clear()
        path = os.path.expanduser('~/Documents/JAM/JAMviewer/' + self.filename)
        self.config.read(path)
        self.machines_info.clear()
        database_manager = DatabaseManager(None, host=self.config.get('Database', 'host'),
                                           port=self.config.get('Database', 'port'),
                                           user=self.config.get('Database', 'user'),
                                           password=self.config.get('Database', 'password'),
                                           db=self.config.get('Database', 'db'), create_tables=False)
        self.machines_info = database_manager.get_pis()
        self.logger.debug("Updated Settings")

    def get_ip_key(self, ip, key):
        machine = 'machine{}'.format(key[-1:])
        machine_info = self.machines_info.get(ip, None)
        if machine_info and machine_info.get(machine) and machine_info.get(key):
            return machine_info[machine], machine_info[key]
        else:
            return None

    def get_mac(self, ip, idx):
        if self.machines_info.get(ip):
            return self.machines_info[ip]['mac{}'.format(idx)]
        else:
            return None

    def get_macs(self, ip):
        l = []
        if self.machines_info.get(ip):
            for idx in range(1, 4):
                l.append(self.machines_info[ip]['mac{}'.format(idx)])
            return l
        else:
            return None

    def get_machine(self, ip, idx):
        if self.machines_info.get(ip):
            return self.machines_info[ip]['machine{}'.format(idx)]
        else:
            return None

    def get_ips(self):
        return list(self.machines_info.keys())

    def get_ips_ports(self):
        ip_port_list = []
        for ip in self.machines_info.keys():
            ip_port_tuple = (ip, self.machines_info[ip].get('port', 7777))
            ip_port_list.append(ip_port_tuple)

        return ip_port_list

    def get_port_for(self, ip):
        if self.machines_info.get(ip, None):
            return self.machines_info[ip].get('port', 7777)

        return 7777


class DatabaseManager:
    def __init__(self, settings, host='', user='', password='', db='', port='', lite_db='machine.sqlite',
                 create_tables=False):
        self.logger = logging.getLogger('jamVIEWER')
        self.settings = settings
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        if port.isnumeric():
            port = int(port)
        self.port = port
        self.lite_db = lite_db

        if create_tables:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                self.create_jam_table()
                self.create_jobs_table()
                self.create_emp_table()
                self.create_maintenance_table()
                self.create_emp_shift_table()
                self.create_qc_table()
                self.create_pis_table()
                self.create_machines_table()

        self.logger.info('Complated DatabaseManager __init__')

    def update(self):
        self.host = self.settings.config.get('Database', 'host')
        self.user = self.settings.config.get('Database', 'user')
        self.password = self.settings.config.get('Database', 'password')
        self.db = self.settings.config.get('Database', 'db')
        port = self.settings.config.get('Database', 'port')
        if port.isnumeric():
            self.port = int(port)

    @staticmethod
    def test_db_connection(host, port, user, password, db):
        success = False
        try:
            if port.isnumeric():
                port = int(port)
            conn = pymysql.connect(host=host, user=user, password=password, database=db, port=port)
            if conn.open:
                success = True
        except pymysql.DatabaseError as error:
            logger = logging.getLogger('jamVIEWER')
            logger.error("{}, {}".format(sys._getframe().f_code.co_name, error))

        return success

    def custom_query(self, query, args=''):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        return_list = []

        try:
            with conn.cursor() as cursor:
                if args:
                    cursor.execute(query, args)
                else:
                    cursor.execute(query)
                return_list = cursor.fetchall()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return return_list

    def create_jam_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                # Drop table if it already exist (for testing)
                # cursor.execute("DROP TABLE IF EXISTS jam_current_table;")

                # create JAM table
                sql = "CREATE TABLE IF NOT EXISTS jam_current_table ( " \
                      "machine varchar(10) NOT NULL, " \
                      "jo_no varchar(15) NOT NULL, " \
                      "emp varchar(10) NOT NULL, " \
                      "date_time datetime NOT NULL, " \
                      "shift tinyint(1) unsigned DEFAULT '0', " \
                      "output int(10) unsigned DEFAULT '0', " \
                      "col1 int(11) DEFAULT '0', " \
                      "col2 int(11) DEFAULT '0', " \
                      "col3 int(11) DEFAULT '0', " \
                      "col4 int(11) DEFAULT '0', " \
                      "col5 int(11) DEFAULT '0', " \
                      "col6 int(11) DEFAULT '0', " \
                      "col7 int(11) DEFAULT '0', " \
                      "col8 int(11) DEFAULT '0', " \
                      "col9 int(11) DEFAULT '0', " \
                      "col10 int(11) DEFAULT '0', " \
                      "PRIMARY KEY (machine,jo_no,date_time,emp) );"
                cursor.execute(sql)

                cursor.execute('CREATE TABLE IF NOT EXISTS jam_prev_table LIKE jam_current_table;')
                cursor.execute('CREATE TABLE IF NOT EXISTS jam_past_table LIKE jam_current_table;')

                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

    @staticmethod
    def month_delta(date_, delta):
        m, y = (date_.month + delta) % 12, date_.year + ((date_.month) + delta - 1) // 12
        if not m: m = 12
        d = min(date_.day,
                [31, 29 if y % 4 == 0 and not y % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])

        return date_.replace(day=d, month=m, year=y)

    def get_shift(self, date_time):
        for col in range(1, 5):
            if not self.settings.config.getboolean('Shift', 'shift{}_enable'.format(col)):
                continue

            start_time = datetime.strptime(self.settings.config.get('Shift', 'shift{}_start'.format(col)),
                                           "%H:%M").time()
            end_time = datetime.strptime(self.settings.config.get('Shift', 'shift{}_end'.format(col)), "%H:%M").time()
            if start_time < end_time:
                if start_time <= date_time.time() <= end_time:
                    return col
            else:
                if date_time.time() >= start_time or date_time.time() <= end_time:
                    return col

            return None

    def get_hourly_output(self, start, end, machines_list=None):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        output_list = []

        try:
            with conn.cursor() as cursor:
                query = "SELECT machine, DATE(date_time), HOUR(date_time), SUM(output) FROM jam_current_table " \
                        "WHERE date_time >= %s AND date_time < %s"
                if machines_list:
                    machines_str = str(tuple(machines_list))
                    query = query + " AND machine IN " + machines_str

                query = query + " GROUP BY machine, DATE(date_time), HOUR(date_time);"
                cursor.execute(query, (start, end))
                output_list = cursor.fetchall()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return output_list

    def get_output(self, start, end, machines_list=None):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        output_list = []

        try:
            with conn.cursor() as cursor:
                query1 = "SELECT machine, date_time, output FROM jam_current_table WHERE date_time >= %s " \
                        "AND date_time < %s"
                query2 = "SELECT machine, date_time, output FROM jam_prev_table WHERE date_time >= %s " \
                         "AND date_time < %s"

                if machines_list:
                    machines_str = str(list(machines_list))[1:-1]
                    query1 = query1 + " AND machine IN (" + machines_str + ")"
                    query2 = query2 + " AND machine IN (" + machines_str + ")"

                query = query1 + " UNION ALL " + query2
                query = query + " ORDER BY machine ASC, date_time ASC;"

                cursor.execute(query, (start, end, start, end))
                output_list = cursor.fetchall()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return output_list

    def get_mu(self, start, end, machines_list=None):
        output_list = self.get_output(start, end, machines_list)
        output_dict = {}
        machine = None
        last_machine = None
        current = []

        for machine, date_time, output in output_list:
            if machine not in output_dict:
                if last_machine:
                    current[2] = int((current[1] - current[0]).total_seconds() / 60) + 1
                    output_dict[last_machine].append(current)
                output_dict[machine] = []
                last_machine = machine
                current = [date_time, date_time, 0, output]
            elif current[1] + timedelta(minutes=1) == date_time:
                current[1] = date_time
                current[3] = current[3] + output
            else:
                current[2] = int((current[1] - current[0]).total_seconds() / 60) + 1
                output_dict[machine].append(current)
                current = [date_time, date_time, 0, output]

        if machine:
            current[2] = int((current[1] - current[0]).total_seconds() / 60) + 1
            output_dict[machine].append(current)

        return output_dict

    def find_mu_in_hour(self, start, end, machines_list=None):
        output_list = self.get_output(start, end, machines_list)
        mu_list = []
        if not machines_list:
            machines_list = self.get_machine_names()
        start = datetime.strptime(start, "%Y-%m-%dT%H:%M")
        end = datetime.strptime(end, "%Y-%m-%dT%H:%M")
        time_list = [start] + [start.replace(minute=0) + timedelta(hours=i+1)
                               for i in range(int((end - start).total_seconds()/3600))]
        if end not in time_list:
            time_list = time_list + [end]

        for machine in machines_list:
            for i, time in enumerate(time_list):
                if i == 0:
                    continue
                start1 = time_list[i-1]
                end1 = time
                current = [(value[1], value[2]) for value in output_list
                           if start1 <= value[1] <= end1 and value[0] == machine]
                output_sum = sum(n for _, n in current)
                mu_list.append([machine, output_sum, start1.strftime("%H"), len(current)])

        return mu_list

    def find_missing_in_hour(self, start, end, machines_list=None):
        def get_missing_time(start_time, date_times):
            if start_time:
                duration = 60 - start_time.minute
            else:
                duration = 60

            return int(duration - len(date_times))

        output_list = self.get_output(start, end, machines_list)
        missing_list = []
        if not machines_list:
            machines_list = self.get_machine_names()
        start = datetime.strptime(start, "%Y-%m-%dT%H:%M")
        end = datetime.strptime(end, "%Y-%m-%dT%H:%M")
        time_list = [start] + [start.replace(minute=0) + timedelta(hours=i+1)
                               for i in range(end.hour - start.hour)]
        if end not in time_list:
            time_list = time_list + [end]

        for machine in machines_list:
            for i, time in enumerate(time_list):
                if i == 0:
                    continue
                start1 = time_list[i-1]
                end1 = time
                current = [value[1] for value in output_list if start1 <= value[1] <= end1 and value[0] == machine]
                missed = get_missing_time(start1, current)

                # TODO ammend this later
                missing_list.append([machine, 0, start1.strftime("%H"), missed])

        return missing_list

    def transfer_tables(self):
        self.transfer_table_current_to_prev()
        self.transfer_table_prev_to_past()

    def transfer_table_current_to_prev(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        try:
            with conn.cursor() as cursor:
                today = datetime.today()
                dayofweek = self.settings.config.getint('Data', 'day')
                offset = (today.isoweekday() - dayofweek) % 7
                day_date = today - timedelta(offset)
                query = "INSERT IGNORE INTO jam_past_table (machine, jo_no, emp, date_time, shift, output, col1, col2" \
                        ", col3, col4, col5, col6, col7, col8, col9, col10) SELECT machine, jo_no, emp, " \
                        "DATE_FORMAT(date_time, '%Y-%m-%d %H:00') as new_dt, shift, SUM(output), SUM(col1), SUM(col2)" \
                        ", SUM(col3), SUM(col4), SUM(col5), SUM(col6), SUM(col7), SUM(col8), SUM(col9), SUM(col10) " \
                        "FROM jam_prev_table WHERE date_time < %s - INTERVAL 1 WEEK GROUP BY machine," \
                        " jo_no, emp, new_dt, shift;"
                cursor.execute(query, (day_date,))
                query2 = "DELETE FROM jam_current_table WHERE date_time < %s - INTERVAL 1 WEEK;"
                cursor.execute(query2, (day_date,))
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
            self.logger.warning('Unable to transfer table from current to prev')
        finally:
            conn.close()

    def transfer_table_prev_to_past(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        try:
            with conn.cursor() as cursor:
                today = datetime.today()
                dayofweek = self.settings.config.getint('Data', 'day')
                offset = (today.isoweekday() - dayofweek) % 7 + 7
                day_date = today - timedelta(offset)
                query = "INSERT IGNORE INTO jam_past_table (machine, jo_no, emp, date_time, shift, output, col1, col2" \
                        ", col3, col4, col5, col6, col7, col8, col9, col10) SELECT machine, jo_no, emp, " \
                        "DATE_FORMAT(date_time, '%Y-%m-%d %H:00') as new_dt, shift, SUM(output), SUM(col1), SUM(col2)" \
                        ", SUM(col3), SUM(col4), SUM(col5), SUM(col6), SUM(col7), SUM(col8), SUM(col9), SUM(col10) " \
                        "FROM jam_prev_table WHERE date_time < %s - INTERVAL 2 WEEK GROUP BY machine," \
                        " jo_no, emp, new_dt, shift;"
                cursor.execute(query, (day_date,))
                query2 = "DELETE FROM jam_prev_table WHERE date_time < %s - INTERVAL 2 WEEK;"
                cursor.execute(query2, (day_date,))
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
            self.logger.warning('Unable to transfer table from prev to past')
        finally:
            conn.close()

    def create_emp_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                # TODO check length of the emp_id and name
                # create EMP table
                sql = "CREATE TABLE IF NOT EXISTS emp_table ( " \
                      "emp_id varchar(6) NOT NULL, " \
                      "name varchar(30) DEFAULT NULL, " \
                      "last_modified timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, " \
                      "to_del tinyint(1) unsigned DEFAULT '0', " \
                      "PRIMARY KEY (emp_id));"
                cursor.execute(sql)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def get_emps(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        emp_list = []

        try:
            with conn.cursor() as cursor:
                sql = '''SELECT emp_id, name, last_modified FROM emp_table WHERE to_del = 0;'''
                cursor.execute(sql)
                emp_list = cursor.fetchall()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()
            return emp_list

    def get_last_modified_emp(self, timestamp=None):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        emp_list = []
        if not timestamp:
            timestamp = (datetime.today() - timedelta(days=1)).isoformat(timespec='minutes')

        try:
            with conn.cursor() as cursor:
                sql = 'SELECT emp_id, name, to_del FROM emp_table WHERE last_modified = %s'
                cursor.execute(sql, timestamp)
                emp_list = cursor.fetchall()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()
            return emp_list

    def create_jobs_table(self):
        conn = pymysql.connect(self.host, self.user, self.password, self.db)

        try:
            with conn.cursor() as cursor:
                # TODO check varchar length for each column
                sql = "CREATE TABLE IF NOT EXISTS jobs_table ( " \
                      "umc char(4) DEFAULT NULL, " \
                      "uno char(10) NOT NULL, " \
                      "umachine_no char(15) DEFAULT NULL, " \
                      "usch_qty double DEFAULT NULL, " \
                      "usou_no char(10) DEFAULT NULL, " \
                      "ustk_mc char(4) DEFAULT NULL, " \
                      "ustk char(16) DEFAULT NULL, " \
                      "uraw_mc text, " \
                      "uraw text, " \
                      "uline int(10) unsigned NOT NULL, " \
                      "uuom char(4) DEFAULT NULL, " \
                      "ureq_qty text, " \
                      "ureq_uom text, " \
                      "udraw text, " \
                      "urem mediumtext, " \
                      "ucomplete char(1) DEFAULT NULL, " \
                      "umachine_desc char(40) DEFAULT NULL, " \
                      "ustk_desc1 char(40) DEFAULT NULL, " \
                      "ustk_desc2 char(40) DEFAULT NULL, " \
                      "mname char(40) DEFAULT NULL, " \
                      "trem1 char(40) DEFAULT NULL, " \
                      "tqty int(10) unsigned DEFAULT NULL, " \
                      "tdo_date date DEFAULT NULL, " \
                      "usfc_qty double DEFAULT NULL, " \
                      "last_modified timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, " \
                      "PRIMARY KEY (uno, uline) );"
                cursor.execute(sql)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def create_qc_table(self):
        conn = pymysql.connect(self.host, self.user, self.password, self.db)

        try:
            with conn.cursor() as cursor:
                # TODO check varchar length for emp, machine & jo_no columns
                query = "CREATE TABLE IF NOT EXISTS qc_table ( " \
                        "emp_id varchar(10) NOT NULL, " \
                        "date_time datetime NOT NULL, " \
                        "machine varchar(10) NOT NULL, " \
                        "jo_no varchar(10) NOT NULL, " \
                        "quality tinyint(3) unsigned NOT NULL );"
                cursor.execute(query)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def create_maintenance_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                # TODO check varchar length for emp & machine.
                query = "CREATE TABLE IF NOT EXISTS maintenance_table ( " \
                        "emp_id varchar(10) NOT NULL, " \
                        "machine varchar(10) NOT NULL, " \
                        "start datetime NOT NULL, " \
                        "end datetime DEFAULT NULL, " \
                        "PRIMARY KEY (emp_id, machine, start) );"
                cursor.execute(query)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def create_emp_shift_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                # TODO check varchar length for emp & machine.
                query = 'CREATE TABLE IF NOT EXISTS emp_shift_table ( ' \
                        'emp_id varchar(10) NOT NULL, ' \
                        'machine varchar(10) NOT NULL, ' \
                        'start datetime NOT NULL, ' \
                        'end datetime DEFAULT NULL, ' \
                        'PRIMARY KEY (emp_id,machine,start) );'
                cursor.execute(query)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def create_pis_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = 'CREATE TABLE IF NOT EXISTS pis_table ( ' \
                      'ip varchar(15) NOT NULL, ' \
                      'port smallint(2) unsigned DEFAULT NULL, ' \
                      'nick varchar(15) DEFAULT NULL, machine1 ' \
                      'varchar(15) DEFAULT NULL, ' \
                      'mac1 varchar(5) DEFAULT NULL, ' \
                      'A11 varchar(6) DEFAULT NULL, ' \
                      'A21 varchar(6) DEFAULT NULL, ' \
                      'A31 varchar(6) DEFAULT NULL, ' \
                      'A41 varchar(6) DEFAULT NULL, ' \
                      'A51 varchar(6) DEFAULT NULL, ' \
                      'B11 varchar(6) DEFAULT NULL, ' \
                      'B21 varchar(6) DEFAULT NULL, ' \
                      'B31 varchar(6) DEFAULT NULL, ' \
                      'B41 varchar(6) DEFAULT NULL, ' \
                      'B51 varchar(6) DEFAULT NULL, ' \
                      'machine2 varchar(15) DEFAULT NULL, ' \
                      'mac2 varchar(5) DEFAULT NULL, ' \
                      'A12 varchar(6) DEFAULT NULL, ' \
                      'A22 varchar(6) DEFAULT NULL, ' \
                      'A32 varchar(6) DEFAULT NULL, ' \
                      'A42 varchar(6) DEFAULT NULL, ' \
                      'A52 varchar(6) DEFAULT NULL, ' \
                      'B12 varchar(6) DEFAULT NULL, ' \
                      'B22 varchar(6) DEFAULT NULL, ' \
                      'B32 varchar(6) DEFAULT NULL, ' \
                      'B42 varchar(6) DEFAULT NULL, ' \
                      'B52 varchar(6) DEFAULT NULL, ' \
                      'machine3 varchar(15) DEFAULT NULL, ' \
                      'mac3 varchar(5) DEFAULT NULL, ' \
                      'A13 varchar(6) DEFAULT NULL, ' \
                      'A23 varchar(6) DEFAULT NULL, ' \
                      'A33 varchar(6) DEFAULT NULL, ' \
                      'A43 varchar(6) DEFAULT NULL, ' \
                      'A53 varchar(6) DEFAULT NULL, ' \
                      'B13 varchar(6) DEFAULT NULL, ' \
                      'B23 varchar(6) DEFAULT NULL, ' \
                      'B33 varchar(6) DEFAULT NULL, ' \
                      'B43 varchar(6) DEFAULT NULL, ' \
                      'B53 varchar(6) DEFAULT NULL, ' \
                      'ludt_to timestamp DEFAULT NULL, ' \
                      'ludt_fr timestamp DEFAULT NULL, ' \
                      'ludt_jobs timestamp DEFAULT NULL, ' \
                      'PRIMARY KEY (ip) );'
                cursor.execute(sql)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def get_last_updates(self, ip):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        last_updates = None

        try:
            with conn.cursor() as cursor:
                sql = 'SELECT ludt_to, ludt_fr, ludt_jobs FROM pis_table WHERE ip = %s'
                cursor.execute(sql, [ip, ])
                last_updates = cursor.fetchone()
            conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

        return last_updates

    def get_pis(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        pis_dict = {}

        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute('SELECT * FROM pis_table;')
                for row in cursor:
                    ip = row.pop('ip')
                    row['port'] = str(row['port'])
                    pis_dict[ip] = row
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return pis_dict

    def update_ludt_fr(self, ip):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE pis_table SET ludt_fr = NOW() WHERE ip = '{}';".format(ip))
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

    def update_ludt_jobs(self, ip):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE pis_table SET ludt_jobs = NOW() WHERE ip = '{}';".format(ip))
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

    def create_machines_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = "CREATE TABLE IF NOT EXISTS machines_table ( " \
                      "machine varchar(10) NOT NULL, " \
                      "output int(10) unsigned DEFAULT NULL, " \
                      "col1 int(11) DEFAULT NULL, " \
                      "col2 int(11) DEFAULT NULL, " \
                      "col3 int(11) DEFAULT NULL, " \
                      "col4 int(11) DEFAULT NULL, " \
                      "col5 int(11) DEFAULT NULL, " \
                      "col6 int(11) DEFAULT NULL, " \
                      "col7 int(11) DEFAULT NULL, " \
                      "col8 int(11) DEFAULT NULL, " \
                      "col9 int(11) DEFAULT NULL, " \
                      "col10 int(11) DEFAULT NULL, " \
                      "PRIMARY KEY (machine) );"
                cursor.execute(sql)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def get_machines_headers(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        headers_list = []

        try:
            with conn.cursor() as cursor:
                sql = 'SHOW COLUMNS FROM machines_table;'
                cursor.execute(sql)
                for row in cursor:
                    headers_list.append(row[0])
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return headers_list

    def get_machines(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        machines_list = []

        try:
            with conn.cursor() as cursor:
                sql = 'SELECT * FROM machines_table;'
                cursor.execute(sql)
                machines_list = cursor.fetchall()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return machines_list

    def get_machine_names(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        machines_list = []

        try:
            with conn.cursor() as cursor:
                sql = 'SELECT machine FROM machines_table;'
                cursor.execute(sql)
                for row in cursor:
                    machines_list.append(row[0])
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return machines_list

    def get_machine_targets(self, col, machines_list=None):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        targets_dict = {}
        try:
            with conn.cursor() as cursor:
                query = "SELECT machine, " + col + " FROM machines_table"
                if machines_list:
                    machines_str = str(tuple(machines_list))
                    query = query + " WHERE machine IN " + machines_str
                query = query + ";"

                cursor.execute(query)
                for row in cursor:
                    targets_dict[row[0]] = row[1]
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return targets_dict

    def create_sfu_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = "CREATE TABLE IF NOT EXISTS sfu_table ( " \
                      "umc char(4) DEFAULT NULL, " \
                      "uno char(10) NOT NULL, " \
                      "uline int(10) unsigned NOT NULL, " \
                      "umachine_no char(15) DEFAULT NULL, " \
                      "usfc_qty double DEFAULT NULL, " \
                      "usfc_emp1 char(10) DEFAULT NULL, " \
                      "usfc_emp2 char(10) DEFAULT NULL, " \
                      "usfc_emp3 char(10) DEFAULT NULL, " \
                      "usfc_qty_waste1 double DEFAULT NULL, " \
                      "usfc_qty_waste2 double DEFAULT NULL, " \
                      "usfc_date date DEFAULT NULL, " \
                      "usfc_time_fr time DEFAULT NULL, " \
                      "usfc_time_to time DEFAULT NULL);"
                cursor.execute(sql)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def get_sfu_headers(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        headers_list = []

        try:
            with conn.cursor() as cursor:
                query = "SHOW COLUMNS FROM sfu_table;"
                cursor.execute(query)
                for row in cursor:
                    headers_list.append(row[0])
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return headers_list

    def get_sfus(self, date=None, time_fr=None, time_to=None, machines_list=None):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        sfu_list = []

        try:
            with conn.cursor() as cursor:
                query = "SELECT * FROM sfu_table"
                conditions = []
                if date:
                    conditions.append("usfc_date = '{}'".format(date))
                if time_fr:
                    conditions.append("usfc_time_fr > '{}'".format(time_fr))
                if time_to:
                    conditions.append("usfc_time_to < '{}'".format(time_to))
                if machines_list:
                    machines_str = str(tuple(machines_list))
                    conditions.append("machine IN ".format(machines_str))

                query = query + ' WHERE ' + ' AND '.join(conditions)
                cursor.execute(query)
                sfu_list = cursor.fetchall()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return sfu_list


if __name__ == '__main__':
    settings_ = Settings()
    # print(settings_.get_ips_ports())
    db_manager = DatabaseManager(settings_, password='Lim8699', db='test')
