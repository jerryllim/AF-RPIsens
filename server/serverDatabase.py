import sys
import csv
import pymysql
import warnings
import configparser
from datetime import datetime, timedelta
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler


class Settings:
    def __init__(self, filename='jam.ini'):
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.config.read(self.filename)
        self.machines_info = {}
        self.update()

    def update(self):
        self.config.clear()
        self.config.read(self.filename)
        self.machines_info.clear()
        database_manager = DatabaseManager(None, host=self.config.get('Database', 'host'),
                                           port=self.config.get('Database', 'port'),
                                           user=self.config.get('Database', 'user'),
                                           password=self.config.get('Database', 'password'),
                                           db=self.config.get('Database', 'db'), create_tables=False)
        self.machines_info = database_manager.get_pis()

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


class AutomateSchedulers:
    def __init__(self, settings: Settings, database_manager):
        self.settings = settings
        self.database_manager = database_manager
        self.scheduler_jobs = {}
        self.scheduler = BackgroundScheduler()
        # self.scheduler.start()

    def get_cron_hour_minute(self, section):
        time = self.settings.config.get(section, 'time')
        hour = self.settings.config.getint(section, 'hour')
        minute = self.settings.config.getint(section, 'minute')
        if hour:
            hour = '*/{}'.format(hour)
        else:
            hour = '*'

        if minute:
            minute = '{}-59/{}'.format(time[-2:], minute)
        else:
            minute = '{}'.format(time[-2:])

        return hour, minute

    def schedule_import(self):
        job_id = 'Import'
        hour, minute = self.get_cron_hour_minute(job_id)
        cron_trigger = CronTrigger(hour=hour, minute=minute)
        if self.scheduler_jobs.get(job_id):
            self.scheduler_jobs[job_id].remove()
        self.scheduler_jobs[job_id] = self.scheduler.add_job(self.read_import_file, cron_trigger, id=job_id,
                                                             max_instances=3)

    def read_import_file(self):
        filepath = self.settings.config.get('Import', 'path')
        with open(filepath, 'r') as import_file:
            csv_reader = csv.reader(import_file)

            next(csv_reader)
            self.database_manager.replace_jobs(csv_reader)

        self.database_manager.delete_completed_jobs()

    def schedule_export(self):
        job_id = 'Export'
        hour, minute = self.get_cron_hour_minute(job_id)
        cron_trigger = CronTrigger(hour=hour, minute=minute)
        if self.scheduler_jobs.get(job_id):
            self.scheduler_jobs[job_id].remove()
        self.scheduler_jobs[job_id] = self.scheduler.add_job(self.read_import_file, cron_trigger, id=job_id,
                                                             max_instances=3)

    def write_export_file(self):
        filepath = self.settings.config.get('Export', 'path') + 'export_jam.csv'
        with open(filepath, 'a') as export_file:
            csv_writer = csv.writer(export_file)

            pass


class DatabaseManager:
    def __init__(self, settings, host='', user='', password='', db='', port='', create_tables=True):
        self.settings = settings
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        if port.isnumeric():
            port = int(port)
        self.port = port

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

    @staticmethod
    def test_db_connection(host, port, user, password, db):
        success = False
        try:
            if port.isnumeric():
                port = int(port)
            conn = pymysql.connect(host=host, user=user, password=password, database=db, port=port)
            if conn.open:
                success = True
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)

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
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
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
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()

    def insert_jam(self, ip, recv_dict):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                for recv_id, recv_info in recv_dict.items():
                    emp, job, time_str = recv_id.split('_', 3)
                    recv_time = datetime.strptime(time_str, '%H%M')
                    now = datetime.now()
                    date_time = now.replace(hour=recv_time.hour, minute=recv_time.minute)
                    if recv_time.time() > now.time():
                        date_time = date_time - timedelta(1)
                    # TODO get shift base on time

                    for key in recv_info.keys():
                        values = self.settings.get_ip_key(ip, key)

                        if values:
                            query = "INSERT INTO jam_current_table (machine, jo_no, emp, date_time, " \
                                    "{header}) VALUES ('{machine}', '{jo_no}', '{emp}', '{date_time}', {value}) ON " \
                                    "DUPLICATE KEY UPDATE {header} = {header} + {value};".format(header=values[1],
                                                                                                 machine=values[0],
                                                                                                 jo_no=job, emp=emp,
                                                                                                 date_time=date_time.strftime(
                                                                                                     "%Y-%m-%d %H:%M"),
                                                                                                 value=recv_info[key])
                            cursor.execute(query)
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()

    def get_output(self, start, end, machines_list=None):
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
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()
            return output_list

    def transfer_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                # TODO to check this sql
                sql = "INSERT IGNORE INTO jam_past_table (machine, jo_no, emp, date_time, shift, output, col1, col2, " \
                      "col3, col4, col5, col6, col7, col8, col9, col10) SELECT * FROM jam_current_table " \
                      "WHERE datetime < NOW() - INTERVAL 2 WEEK;"
                cursor.execute(sql)
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
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
                      "last_modified timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, " \
                      "to_del tinyint(1) unsigned DEFAULT '0', " \
                      "PRIMARY KEY (emp_id));"
                cursor.execute(sql)
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            conn.close()

    def insert_emp(self, emp_id, emp_name):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        try:
            with conn.cursor() as cursor:
                sql = "REPLACE INTO emp_table (emp_id, name) VALUES (%s, %s);"
                cursor.execute(sql, (emp_id, emp_name, emp_name))
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()

    def insert_emps(self, emp_list):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        try:
            with conn.cursor() as cursor:
                sql = "REPLACE INTO emp_table (emp_id, name) VALUES (%s, %s);"
                # new_list = [(row[0], row[1], row[1]) for row in emp_list]
                cursor.executemany(sql, emp_list)

                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()

    def mark_to_delete_emp(self, emp_ids):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        emp_str = str(tuple(emp_ids))
        if len(emp_ids) == 1:
            emp_str = emp_str.replace(',', '')

        try:
            with conn.cursor() as cursor:
                sql = 'UPDATE emp_table SET to_del = 1 WHERE emp_id IN ' + str(emp_str) + ';'
                cursor.execute(sql)
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()

    def delete_emp(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = '''DELETE emp_table WHERE to_del = 1'''
                cursor.execute(sql)
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
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
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
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
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            conn.close()
            return emp_list

    def create_jobs_table(self):
        db = pymysql.connect(self.host, self.user, self.password, self.db)

        try:
            with db.cursor() as cursor:
                # TODO check varchar length for each column
                sql = "CREATE TABLE IF NOT EXISTS jobs_table ( " \
                      "umc char(4) DEFAULT NULL, " \
                      "uno char(10) DEFAULT NULL, " \
                      "umachine_no char(15) DEFAULT NULL, " \
                      "usch_qty double DEFAULT NULL, " \
                      "usou_no char(10) DEFAULT NULL, " \
                      "ustk_mc char(4) DEFAULT NULL, " \
                      "ustk char(16) DEFAULT NULL, " \
                      "uraw_mc text, " \
                      "uraw text, " \
                      "uline int(10) unsigned DEFAULT NULL, " \
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
                      "tdo_date date DEFAULT NULL );"
                cursor.execute(sql)
                db.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            db.close()

    def replace_jobs(self, job_list):
        """
        Call to insert job from eb to database
        :param job_list: list containing tuples. A tuple will contain the job information e.g. ('job#', 'mac', ...,
        'so_rem')
        :return:
        """
        db = pymysql.connect(self.host, self.user, self.password, self.db)
        # column_names = ['jo_no', 'jo_line', 'mac', 'to_do', 'code', 'descp', 'so_no', 'edd', 'so_qty', 'so_rem']
        # column_names_str = ', '.join(column_names)
        # binds_str = ', '.join(['%s'] * len(column_names))
        try:
            with db.cursor() as cursor:
                for job_info in job_list:
                    query = "REPLACE INTO jobs_table VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                            "%s, %s, %s, %s, %s, %s, %s, %s, STR_TO_DATE(%s, %s));"
                    job_info = job_info + ["%d/%m/%Y"]
                    cursor.execute(query, job_info)
                    db.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            db.rollback()
        finally:
            db.close()

    def delete_completed_jobs(self):
        db = pymysql.connect(self.host, self.user, self.password, self.db)
        try:
            with db.cursor() as cursor:
                query = "DELETE FROM job_info WHERE ucomplete = 'Y';"
                cursor.execute(query)
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            db.close()

    def delete_job(self, jo_ids):
        """
        Delete multiple jobs
        :param jo_ids: List of jo_no & jo_line
        :return:
        """
        db = pymysql.connect(self.host, self.user, self.password, self.db)
        try:
            with db.cursor() as cursor:
                query = '''DELETE FROM job_info WHERE jo_no = %s AND jo_line = %s'''
                cursor.executemany(query, jo_ids)
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            db.close()

    def get_job_info(self, barcode):
        db = pymysql.connect(self.host, self.user, self.password, self.db)
        cursor = db.cursor()
        reply_str = []
        try:
            jo_no = barcode[:-3]
            jo_line = int(barcode[-3:])
            sql = "SELECT uno, uline, usou_no, ustk_desc1, usch_qty, 0 FROM jobs_table " \
                  "WHERE uno = %s AND uline = %s LIMIT 1"
            cursor.execute(sql, (jo_no, jo_line))
            temp = cursor.fetchone()
            reply_str = list(temp)
            db.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            db.close()
            return reply_str

    def get_jobs_for(self, mac):
        db = pymysql.connect(self.host, self.user, self.password, self.db)
        job_list = []
        try:
            with db.cursor() as cursor:
                sql = '''SELECT * FROM jobs_table WHERE umachine_no = %s'''
                cursor.execute(sql, (mac,))
                for row in cursor:
                    job_list.append(row)
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            db.close()
            return job_list

    @staticmethod
    def check_complete(cursor, jo_id, jo_line):
        query = '''DELETE FROM job_info WHERE jo_no = %s AND jo_line = %s AND ran >= to_do'''
        cursor.execute(query, (jo_id, jo_line))

    def create_qc_table(self):
        db = pymysql.connect(self.host, self.user, self.password, self.db)

        try:
            with db.cursor() as cursor:
                # TODO check varchar length for emp, machine & jo_no columns
                query = "CREATE TABLE IF NOT EXISTS qc_table ( " \
                        "emp_id varchar(10) NOT NULL, " \
                        "date_time datetime NOT NULL, " \
                        "machine varchar(10) NOT NULL, " \
                        "jo_no varchar(10) NOT NULL, " \
                        "quality tinyint(3) unsigned NOT NULL );"
                cursor.execute(query)
                db.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            db.close()

    def insert_qc(self, machine, values):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password,
                             database=self.db, port=self.port)

        try:
            with db.cursor() as cursor:
                for value in values:
                    emp, jo_no, time_str, grade = value.split('_', 4)
                    recv_time = datetime.strptime(time_str, '%H%M')
                    now = datetime.now()
                    date_time = now.replace(hour=recv_time.hour, minute=recv_time.minute)
                    if recv_time.time() > now.time():
                        date_time = date_time - timedelta(1)

                    query = 'INSERT INTO qc_table (emp_id, date_time, machine, jo_no, quality) VALUES ({emp}, ' \
                            '{date_time}, {machine}, {jo_no}, ' \
                            '{grade})'.format(emp=emp, date_time=date_time.strftime("%Y-%m-%d %H:%M"),
                                              machine=machine, jo_no=jo_no, grade=grade)

                    cursor.execute(query)

                db.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            db.close()

    def create_maintenance_table(self):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with db.cursor() as cursor:
                # TODO check varchar length for emp & machine.
                query = "CREATE TABLE IF NOT EXISTS maintenance_table ( " \
                        "emp_id varchar(10) NOT NULL, " \
                        "machine varchar(10) NOT NULL, " \
                        "start datetime NOT NULL, " \
                        "end datetime DEFAULT NULL, " \
                        "PRIMARY KEY (emp_id, machine, start) );"
                cursor.execute(query)
                db.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            db.close()

    def replace_maintenance(self, machine, values):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password,
                             database=self.db, port=self.port)

        try:
            with db.cursor() as cursor:
                for emp_start, end in values.items():
                    emp, start = emp_start.split('_')

                    query = 'REPLACE INTO maintenance_table VALUES (%s, %s, %s, %s);'
                    cursor.execute(query, (emp, machine, start, end))

                db.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            db.close()

    def create_emp_shift_table(self):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password,
                             database=self.db, port=self.port)

        try:
            with db.cursor() as cursor:
                # TODO check varchar length for emp & machine.
                query = 'CREATE TABLE IF NOT EXISTS emp_shift_table ( ' \
                        'emp_id varchar(10) NOT NULL, ' \
                        'machine varchar(10) NOT NULL, ' \
                        'start datetime NOT NULL, ' \
                        'end datetime DEFAULT NULL, ' \
                        'PRIMARY KEY (emp_id,machine,start) );'
                cursor.execute(query)
                db.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            db.close()

    def replace_emp_shift(self, machine, values):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password,
                             database=self.db, port=self.port)

        try:
            with db.cursor() as cursor:
                for emp_start, end in values.items():
                    emp, start = emp_start.split('_')

                    query = 'REPLACE INTO emp_shift_table VALUES (%s, %s, %s, %s);'
                    cursor.execute(query, (emp, machine, start, end))

                db.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            db.close()

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
                      'PRIMARY KEY (ip) );'
                cursor.execute(sql)
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            conn.close()
            
    def saved_all_pis(self, pis_row):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        try:
            with conn.cursor() as cursor:
                sql = 'TRUNCATE pis_table;'
                cursor.execute(sql)

                sql = 'INSERT INTO pis_table VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,' \
                      ' %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
                cursor.executemany(sql, pis_row)
            conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()

    def replace_pi(self, pi_row):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        replaced = False

        try:
            with conn.cursor() as cursor:
                sql = 'REPLACE INTO pis_table VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,' \
                      ' %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
                cursor.execute(sql, pi_row)
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        else:
            replaced = True
        finally:
            conn.close()

        return replaced

    def delete_pi(self, ip):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = 'DELETE pis_table WHERE ip = %s'
                cursor.execute(sql, ip)
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()

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
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()
            return pis_dict

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
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
        finally:
            conn.close()

    def insert_machine(self, machine_row):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = 'INSERT INTO machines_table VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                cursor.execute(sql, machine_row)
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()

    def delete_machines(self, machines):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = 'DELETE FROM machines_table WHERE machine = %s'
                cursor.executemany(sql, machines)
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()

    def reinsert_machines(self, machine_rows):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = 'TRUNCATE machines_table;'
                cursor.execute(sql)

                sql = 'INSERT INTO machines_table VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                cursor.executemany(sql, machine_rows)
                conn.commit()
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
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
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
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
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
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
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
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
                query = "SELECT machine, "+ col +" FROM machines_table"
                if machines_list:
                    machines_str = str(tuple(machines_list))
                    query = query + " WHERE machine IN " + machines_str
                query = query + ";"

                cursor.execute(query)
                for row in cursor:
                    targets_dict[row[0]] = row[1]
        except pymysql.MySQLError as error:
            print(sys._getframe().f_code.co_name, error)
            conn.rollback()
        finally:
            conn.close()
            return targets_dict


if __name__ == '__main__':
    settings_ = Settings()
    # print(settings_.get_ips_ports())
    db_manager = DatabaseManager(settings_, password='Lim8699', db='test')
    AutomateSchedulers(settings_, db_manager)
