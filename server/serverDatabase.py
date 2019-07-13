import os
import csv
import sys
import pymysql
import logging
import warnings
import configparser
from datetime import datetime, timedelta
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler


class Settings:
    def __init__(self, is_server):
        if is_server:
            self.logger_name = "jamSERVER"
            self.log_path = '~/Documents/JAM/JAMserver/jamSERVER.log'
            self.config_path = '~/Documents/JAM/JAMserver/jam.ini'
        else:
            self.logger_name = "jamVIEWER"
            self.log_path = '~/Documents/JAM/JAMviewer/jamVIEWER.log'
            self.config_path = '~/Documents/JAM/JAMviewer/jam.ini'

        self.logger = logging.getLogger(self.logger_name)
        self.config = configparser.ConfigParser()
        path = os.path.expanduser(self.config_path)
        self.config.read(path)
        self.machines_info = {}
        self.update()
        self.logger.info('Completed Settings __init__')

    def update(self):
        self.config.clear()
        path = os.path.expanduser(self.config_path)
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
        try:
            if self.machines_info.get(ip):
                return self.machines_info[ip]['mac{}'.format(idx)]
            else:
                return ''
        except KeyError:
            return ''

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


class AutomateSchedulers:
    def __init__(self, settings, db_dict, logger_name):
        self.logger = logging.getLogger(logger_name)

        self.settings = settings
        self.database_manager = DatabaseManager(settings, **db_dict)
        self.scheduler_jobs = {}
        self.scheduler = BackgroundScheduler()

    def start_scheduler(self):
        self.scheduler.start()
        self.logger.info("Started AutomateSechedulers scheduler")

    def pause_scheduler(self):
        self.scheduler.pause()
        self.logger.info("Paused AutomateSechedulers scheduler")

    def get_cron_hour_minute(self, section):
        if section in ['Export', 'Import']:
            time = self.settings.config.get(section, 'time')
            hour = self.settings.config.getint(section, 'hour')
            minute = self.settings.config.getint(section, 'minute')

            is_odd = int('{}'.format(time[:2])) % 2
            if hour:
                if is_odd:
                    hour = '1-23/{}'.format(hour)
                else:
                    hour = '*/{}'.format(hour)
            else:
                hour = '{}'.format(time[:2])

            if minute:
                minute = '{}-59/{}'.format(time[-2:], minute)
            else:
                minute = '{}'.format(time[-2:])

        elif section in ['Data']:
            time = self.settings.config.get(section, 'time')

            hour = '{}'.format(time[:2])
            minute = '{}'.format(time[-2:])

        else:
            hour = '*'
            minute = '*'

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
        if not os.path.isfile(filepath):
            self.logger.debug('No import file found')
            return

        with open(filepath, 'r') as import_file:
            csv_reader = csv.reader(import_file)

            next(csv_reader)
            self.database_manager.replace_jobs(csv_reader)

        self.database_manager.delete_completed_jobs()
        self.logger.debug('Read import file')

    def schedule_export(self):
        job_id = 'Export'
        hour, minute = self.get_cron_hour_minute(job_id)
        cron_trigger = CronTrigger(hour=hour, minute=minute)
        if self.scheduler_jobs.get(job_id):
            self.scheduler_jobs[job_id].remove()
        self.scheduler_jobs[job_id] = self.scheduler.add_job(self.write_export_file, cron_trigger, id=job_id,
                                                             max_instances=3)

    def write_export_file(self):
        filepath = self.settings.config.get('Export', 'path') + '/export_jam.csv'
        try:
            if not os.path.isfile(filepath):
                with open(filepath, 'w', newline='') as export_file:
                    csv_writer = csv.writer(export_file)
                    csv_writer.writerow(self.database_manager.get_sfu_headers())

            with open(filepath, 'a', newline='') as export_file:
                csv_writer = csv.writer(export_file)
                li = list(self.database_manager.export_sfus())
                csv_writer.writerows(li)

            self.logger.debug("Wrote export file to '{}'".format(filepath))
        except FileNotFoundError as error:
            self.logger.debug("Unable to export to '{}''".format(filepath))

    def schedule_table_transfers(self):
        job_id = 'Data'
        hour, minute = self.get_cron_hour_minute(job_id)
        dayofweek = self.settings.config.get(job_id, 'day')
        cron_trigger = CronTrigger(hour=hour, minute=minute, day_of_week=dayofweek)
        if self.scheduler_jobs.get(job_id):
            self.scheduler_jobs[job_id].remove()
        self.scheduler_jobs[job_id] = self.scheduler.add_job(self.table_transfers, cron_trigger, id=job_id,
                                                             max_instances=3)

    def table_transfers(self):
        self.database_manager.transfer_tables()
        self.logger.debug('Transferred tables')

    def schedule_delete_old_jobs(self):
        job_id = 'Old'
        cron_trigger = CronTrigger(hour='17', minute='35')
        if self.scheduler_jobs.get(job_id):
            self.scheduler_jobs[job_id].remove()
        self.scheduler_jobs[job_id] = self.scheduler.add_job(self.delete_old_jobs, cron_trigger, id=job_id,
                                                             max_instances=3)

    def delete_old_jobs(self):
        self.database_manager.delete_old_jobs()
        self.logger.debug('Deleted old jobs')


class DatabaseManager:
    def __init__(self, settings, host='', user='', password='', db='', port='', create_tables=True,
                 log_name="jamSERVER"):
        self.logger = logging.getLogger(log_name)
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
                self.create_sfu_table()

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
            logger = logging.getLogger('jamSERVER')
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

    def insert_jam(self, ip, recv_dict):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                seq = recv_dict.pop('seq', None)
                if seq is None or not isinstance(seq, int):
                    self.logger.debug("No sequence or invalid sequence ({}). Abort insert jam from {}".format(seq, ip))
                    return

                # Update the 'ludt_to' in pis_table (to know the last communication time)
                cursor.execute("UPDATE pis_table SET ludt_to = {} WHERE ip = '{}';".format(seq, ip))
                for recv_id, recv_info in recv_dict.items():
                    emp, job, time_str = recv_id.split('_', 3)
                    recv_time = datetime.strptime(time_str, '%d%H%M')
                    now = datetime.now()
                    date_time = now.replace(day=recv_time.day, hour=recv_time.hour, minute=recv_time.minute)
                    if recv_time.day > now.day:
                        date_time = self.month_delta(date_time, -1)
                    shift = self.get_shift(date_time)

                    for key in recv_info.keys():
                        values = self.settings.get_ip_key(ip, key)

                        if values:
                            query = "INSERT INTO jam_current_table (machine, jo_no, emp, date_time, shift, " \
                                    "{header}) VALUES ('{machine}', '{jo_no}', '{emp}', '{date_time}', %s, " \
                                    "{value}) ON DUPLICATE KEY UPDATE {header} = {header} + " \
                                    "{value};".format(header=values[1], machine=values[0], jo_no=job, emp=emp,
                                                      date_time=date_time.strftime("%Y-%m-%d %H:%M"),
                                                      value=recv_info[key])
                            cursor.execute(query, [shift, ])
                conn.commit()
                self.logger.debug('Inserted jam for {}'.format(ip))
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

    def get_hourly_output_for(self, start, end, machines_list=None):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        output_list = []

        try:
            with conn.cursor() as cursor:
                query = "SELECT machine, DATE(date_time), HOUR(date_time), SUM(output) FROM jam_current_table " \
                        "WHERE date_time >= %s AND date_time < %s"
                if machines_list:
                    machines_str = str(list(machines_list))[1:-1]
                    query = query + " AND machine IN (" + machines_str + ")"

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
                date_str = day_date.strftime('%Y-%m-%d')
                query = "INSERT IGNORE INTO jam_prev_table SELECT * FROM jam_current_table WHERE date_time < %s " \
                        "- INTERVAL 1 WEEK;"
                cursor.execute(query, (date_str,))
                query2 = "DELETE FROM jam_current_table WHERE date_time < %s - INTERVAL 1 WEEK;"
                cursor.execute(query2, (date_str,))
                conn.commit()
                self.logger.info('Transferred table from current to prev')
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
                date_str = day_date.strftime('%Y-%m-%d')
                query = "INSERT IGNORE INTO jam_past_table (machine, jo_no, emp, date_time, shift, output, col1, col2" \
                        ", col3, col4, col5, col6, col7, col8, col9, col10) SELECT machine, jo_no, emp, " \
                        "DATE_FORMAT(date_time, '%Y-%m-%d %H:00') as new_dt, shift, SUM(output), SUM(col1), SUM(col2)" \
                        ", SUM(col3), SUM(col4), SUM(col5), SUM(col6), SUM(col7), SUM(col8), SUM(col9), SUM(col10) " \
                        "FROM jam_prev_table WHERE date_time < %s - INTERVAL 2 WEEK GROUP BY machine," \
                        " jo_no, emp, new_dt, shift;"
                cursor.execute(query, (date_str,))
                query2 = "DELETE FROM jam_prev_table WHERE date_time < %s - INTERVAL 2 WEEK;"
                cursor.execute(query2, (date_str,))
                conn.commit()
                self.logger.info('Transferred table from prev to past')
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

    def insert_emp(self, emp_id, emp_name):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        try:
            with conn.cursor() as cursor:
                sql = "REPLACE INTO emp_table (emp_id, name) VALUES (%s, %s);"
                cursor.execute(sql, (emp_id, emp_name, emp_name))
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
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
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
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
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
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
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
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

    def replace_jobs(self, job_list):
        """
        Call to insert job from eb to database
        :param job_list: list containing tuples. A tuple will contain the job information e.g. ('job#', 'mac', ...,
        'so_rem')
        :return:
        """
        conn = pymysql.connect(self.host, self.user, self.password, self.db)
        try:
            with conn.cursor() as cursor:
                for job_info in job_list:
                    query = "REPLACE INTO jobs_table (umc, uno, umachine_no, usch_qty, usou_no, ustk_mc, ustk, " \
                            "uraw_mc, uraw, uline, uuom, ureq_qty, ureq_uom, udraw, urem, ucomplete, umachine_desc, " \
                            "ustk_desc1, ustk_desc2, mname, trem1, tqty, tdo_date, usfc_qty)" \
                            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                            "%s, %s, %s, %s, %s, %s, %s, %s, STR_TO_DATE(%s, '%%d/%%m/%%Y'), %s);"
                    cursor.execute(query, job_info)
                    conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

    def delete_completed_jobs(self):
        conn = pymysql.connect(self.host, self.user, self.password, self.db)

        try:
            with conn.cursor() as cursor:
                query = "DELETE FROM jobs_table WHERE ucomplete = 'Y';"
                cursor.execute(query)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

    def delete_old_jobs(self):
        conn = pymysql.connect(self.host, self.user, self.password, self.db)

        try:
            with conn.cursor() as cursor:
                query = "DELETE FROM jobs_table WHERE usfc_qty >= usch_qty AND " \
                        "last_modified < (CURDATE() - INTERVAL 3 DAY);"
                cursor.execute(query)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

    def get_job_info(self, barcode):
        conn = pymysql.connect(self.host, self.user, self.password, self.db)
        cursor = conn.cursor()
        reply_list = []
        try:
            jo_no = barcode[:-3]
            jo_line = int(barcode[-3:])
            sql = "SELECT uno, uline, ustk, ustk_desc1, usch_qty, uuom, usfc_qty FROM jobs_table " \
                  "WHERE uno = %s AND uline = %s LIMIT 1;"
            if cursor.execute(sql, (jo_no, jo_line)):
                temp = cursor.fetchone()
                reply_list = list(temp)

            conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()
            return reply_list

    def get_umc_for(self, uno, uline):
        conn = pymysql.connect(self.host, self.user, self.password, self.db)
        umc = ''

        try:
            with conn.cursor() as cursor:
                sql = "SELECT umc FROM jobs_table WHERE uno = %s AND uline = %s;"
                if cursor.execute(sql, [uno, uline]):
                    umc = cursor.fetchone()[0]
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

        return umc

    def update_job(self, uno, uline, usfc_qty):
        conn = pymysql.connect(self.host, self.user, self.password, self.db)

        try:
            with conn.cursor() as cursor:
                query = "UPDATE jobs_table SET usfc_qty = usfc_qty + %s WHERE uno = %s AND uline = %s;"
                cursor.execute(query, (usfc_qty, uno, uline))
                conn.commit()
                self.logger.debug("Updated jobs_table with {}, {} and {}".format(uno, uline, usfc_qty))
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

    def get_jobs_for_in(self, macs, dt=0):
        conn = pymysql.connect(self.host, self.user, self.password, self.db)
        job_list = []
        now = datetime.now()
        if not isinstance(macs, list):
            macs = [macs]

        try:
            with conn.cursor() as cursor:
                sql = "SELECT uno, uline, ustk, ustk_desc1, usch_qty, uuom, usfc_qty FROM jobs_table WHERE " \
                      "umachine_no IN %s"
                if dt:
                    sql = sql + " AND last_modified >= '{}' AND " \
                                "last_modified <= '{}';".format(dt, now.strftime("%Y-%m-%d %H:%M:%S"))
                cursor.execute(sql, (macs,))
                for row in cursor:
                    job_list.append(row)
                new_dt = int(now.timestamp())
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()
            return new_dt, job_list

    def get_jobs_for_like(self, mac, dt=0):
        conn = pymysql.connect(self.host, self.user, self.password, self.db)
        job_list = []
        now = datetime.now()
        mac = mac + '%'

        try:
            with conn.cursor() as cursor:
                sql = "SELECT uno, uline, ustk, ustk_desc1, usch_qty, uuom, usfc_qty FROM jobs_table WHERE " \
                      "umachine_no LIKE %s"
                if dt:
                    sql = sql + " AND last_modified >= '{}' AND " \
                                "last_modified <= '{}';".format(dt, now.strftime("%Y-%m-%d %H:%M:%S"))
                cursor.execute(sql, (mac,))
                for row in cursor:
                    job_list.append(row)
                new_dt = int(now.timestamp())
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()
            return new_dt, job_list

    @staticmethod
    def check_complete(cursor, jo_id, jo_line):
        query = '''DELETE FROM jobs_table WHERE jo_no = %s AND jo_line = %s AND ran >= to_do'''
        cursor.execute(query, (jo_id, jo_line))

    def create_qc_table(self):
        conn = pymysql.connect(self.host, self.user, self.password, self.db)

        try:
            with conn.cursor() as cursor:
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

    def insert_qc(self, machine, values):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                for value in values:
                    emp, jo_no, time_str, grade = value.split('_', 4)
                    recv_time = datetime.strptime(time_str, '%d%H%M')
                    now = datetime.now()
                    date_time = now.replace(day=recv_time.day, hour=recv_time.hour, minute=recv_time.minute)
                    if recv_time.day > now.day:
                        date_time = self.month_delta(date_time, -1)

                    query = 'INSERT INTO qc_table (emp_id, date_time, machine, jo_no, quality) VALUES ({emp}, ' \
                            '{date_time}, {machine}, {jo_no}, ' \
                            '{grade})'.format(emp=emp, date_time=date_time.strftime("%Y-%m-%d %H:%M"),
                                              machine=machine, jo_no=jo_no, grade=grade)

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

    def replace_maintenance(self, machine, values):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                for emp_start, end_str in values.items():
                    emp, time_str = emp_start.split('_')
                    recv_time = datetime.strptime(time_str, '%d%H%M')
                    now = datetime.now()
                    start = now.replace(day=recv_time.day, hour=recv_time.hour, minute=recv_time.minute)
                    if recv_time.day > now.day:
                        start = self.month_delta(start, -1)

                    if end_str:
                        end_time = datetime.strptime(end_str, '%d%H%M')
                        end = now.replace(day=end_time.day, hour=end_time.hour, minute=end_time.minute)
                        if end_time.day > now.day:
                            end = self.month_delta(end, -1)
                    else:
                        end = None

                    query = 'REPLACE INTO maintenance_table VALUES (%s, %s, %s, %s);'
                    cursor.execute(query, (emp, machine, start, end))

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

    def replace_emp_shift(self, machine, values):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        if not machine:
            return

        try:
            with conn.cursor() as cursor:
                for emp_start, end_str in values.items():
                    emp, time_str = emp_start.split('_')
                    recv_time = datetime.strptime(time_str, '%d%H%M')
                    now = datetime.now()
                    start = now.replace(day=recv_time.day, hour=recv_time.hour, minute=recv_time.minute)
                    if recv_time.day > now.day:
                        start = self.month_delta(start, -1)

                    if end_str:
                        end_time = datetime.strptime(end_str, '%d%H%M')
                        end = now.replace(day=end_time.day, hour=end_time.hour, minute=end_time.minute)
                        if end_time.day > now.day:
                            end = self.month_delta(end, -1)
                    else:
                        end = None

                    query = 'REPLACE INTO emp_shift_table VALUES (%s, %s, %s, %s);'
                    cursor.execute(query, (emp, machine, start, end))

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
                      'ludt_to int(11) DEFAULT 0, ' \
                      'ludt_fr int(11) DEFAULT 0, ' \
                      'ludt_jobs int(11) DEFAULT 0, ' \
                      'PRIMARY KEY (ip) );'
                cursor.execute(sql)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def saved_all_pis(self, pis_row):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        try:
            with conn.cursor() as cursor:
                ips = []

                for row in pis_row:
                    ips.append(row[0])
                    last = self.get_last_updates_posix(row[0])
                    if last:
                        row.append(last[0])
                        row.append(last[1])
                        row.append(last[2])
                    else:
                        row.append(0)
                        row.append(0)
                        row.append(0)

                sql = 'REPLACE INTO pis_table VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ' \
                      '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ' \
                      '%s, %s, %s);'
                cursor.executemany(sql, pis_row)

                sql = "DELETE FROM pis_table WHERE ip NOT IN %s"
                cursor.execute(sql, (ips,))
            conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

    def get_last_updates_posix(self, ip):
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

    def get_last_updates(self, ip):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        last_updates = None

        try:
            with conn.cursor() as cursor:
                sql = 'SELECT ludt_to, ludt_fr, ludt_jobs FROM pis_table WHERE ip = %s'
                cursor.execute(sql, [ip, ])
                last_posix = cursor.fetchone()
                if last_posix:
                    last_updates = []
                    for ts in last_posix:
                        last_updates.append(datetime.fromtimestamp(ts))

            conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

        return last_updates

    def delete_pi(self, ip):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = 'DELETE pis_table WHERE ip = %s'
                cursor.execute(sql, [ip, ])
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
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
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return pis_dict

    def update_ludt_fr(self, ip, dt=None):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                if dt is None:
                    dt = datetime.now().timestamp()

                dt = int(dt)
                cursor.execute("UPDATE pis_table SET ludt_fr = {} WHERE ip = '{}';".format(dt, ip))
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        except ValueError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

    def update_ludt_jobs(self, ip, dt):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                dt = int(dt)
                cursor.execute("UPDATE pis_table SET ludt_jobs = {} WHERE ip = '{}';".format(dt, ip))
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        except ValueError as error:
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

    def insert_machine(self, machine_row):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = 'INSERT INTO machines_table VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                cursor.execute(sql, machine_row)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
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
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
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

                sql = 'INSERT INTO machines_table VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                cursor.executemany(sql, machine_rows)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
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
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return headers_list

    def get_distinct_workcenters(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        workcenters_list = []

        try:
            with conn.cursor() as cursor:
                query = "SELECT DISTINCT(wc) FROM machines_table;"
                cursor.execute(query)
                for row in cursor:
                    workcenters_list.append(row[0])
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return workcenters_list

    def get_machines_in(self, workcenters):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        machines_list = []
        is_null = False

        try:
            with conn.cursor() as cursor:
                if None in workcenters:
                    workcenters.remove(None)
                    is_null = True
                workcenters_str = str(list(workcenters))[1:-1]
                query = "SELECT machines FROM machines_table WHERE wc IN (" + workcenters_str + ")"
                if is_null:
                    query = query + " OR wc IS NULL;"
                elif isinstance(workcenters, list):
                    query = query + " WHERE wc IS NULL"

                cursor.execute(query)
                for row in cursor:
                    machines_list.append(row[0])
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return machines_list

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

    def get_machine_workcenters_names(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        machines_list = []

        try:
            with conn.cursor() as cursor:
                sql = 'SELECT wc, machine FROM machines_table;'
                cursor.execute(sql)
                machines_list = list(cursor.fetchall())
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return machines_list

    def get_machine_workcenters_names_for(self, workcenters=None):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        machines_list = []
        is_null = False

        try:
            with conn.cursor() as cursor:
                query = 'SELECT wc, machine FROM machines_table'
                if any(workcenters):
                    if None in workcenters:
                        workcenters.remove(None)
                        is_null = True
                    workcenters = str(list(workcenters))[1:-1]
                    query = query + " WHERE wc IN (" + workcenters +")"
                    if is_null:
                        query = query + " OR wc IS NULL"
                elif isinstance(workcenters, list):
                    query = query + " WHERE wc IS NULL"

                cursor.execute(query)
                machines_list = list(cursor.fetchall())
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return machines_list

    def get_machine_workcenters(self):
        machines_list = self.get_machine_workcenters_names()
        machines_dict = {}
        for wc, machine in machines_list:
            machines_dict[machine] = wc

        return machines_dict

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
                      "usfc_qty double DEFAULT 0, " \
                      "usfc_emp1 char(10) DEFAULT NULL, " \
                      "usfc_emp2 char(10) DEFAULT NULL, " \
                      "usfc_emp3 char(10) DEFAULT NULL, " \
                      "usfc_qty_waste1 double DEFAULT NULL, " \
                      "usfc_qty_waste2 double DEFAULT NULL, " \
                      "usfc_date date DEFAULT NULL, " \
                      "usfc_time_fr time DEFAULT NULL, " \
                      "usfc_time_to time DEFAULT NULL);"
                cursor.execute(sql)
                query2 = "SELECT 1 FROM `INFORMATION_SCHEMA`.`STATISTICS` WHERE `TABLE_SCHEMA` = '%s' AND " \
                         "`TABLE_NAME` = 'sfu_table' AND `INDEX_NAME` = 'distinct_idx';"
                cursor.execute(query2)
                if cursor.fetchone():
                    query3 = "CREATE UNIQUE INDEX distinct_idx ON sfu_table(umc, uno, uline, umachine_no, usfc_qty, " \
                             "usfc_emp1, usfc_emp2, usfc_emp3, usfc_qty_waste1, usfc_qty_waste2, usfc_date, " \
                             "usfc_time_fr, usfc_time_to);"
                    cursor.execute(query3)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def insert_sfu(self, sfu):
        """
        Inserts sfu to the table
        """
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                query = "INSERT INTO sfu_table VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                cursor.execute(query, sfu)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def get_sfu_headers(self):
        """
        Get sfu table headers (Used for SFUDisplayTable)
        :return:
        """
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
        """
        Get the sfus without deleting them
        :return: sfu as list
        """
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
                    conditions.append("machine IN {}".format(machines_str))

                if conditions:
                    query = query + ' WHERE ' + ' AND '.join(conditions)
                cursor.execute(query)
                sfu_list = cursor.fetchall()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return sfu_list

    def export_sfus(self, date=None, time_fr=None, time_to=None, machines_list=None):
        """
        Get & deletes sfus in the table while locking the table to prevent deleting un-exported data
        :return: The deleted sfus
        """
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        sfu_list = []

        try:
            with conn.cursor() as cursor:
                query = "LOCK TABLE sfu_table WRITE;"
                cursor.execute(query)
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
                    conditions.append("machine IN {}".format(machines_str))

                if conditions:
                    query = query + ' WHERE ' + ' AND '.join(conditions)
                cursor.execute(query)
                sfu_list = cursor.fetchall()
                query = "DELETE FROM sfu_table;"
                cursor.execute(query)
                query = "UNLOCK TABLES"
                cursor.execute(query)

                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()
            return sfu_list

    def create_uom_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                query = "CREATE TABLE uom_table (ustk char(16) NOT NULL, ustk_desc1 char(40) DEFAULT NULL, " \
                        "muom_p char(3) NOT NULL, multiplier double NOT NULL DEFAULT 1)"
                cursor.execute(query)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()

    def replace_uom(self, uom_list):
        """
        Replaces row in uom_table
        :param uom_list: Row to insert
        """
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        try:
            with conn.cursor() as cursor:
                query = "REPLACE INTO uom_table (ustk, ustk_desc1, muom_p, multiplier) VALUES (%s, %s, %s, %s);"
                cursor.executemany(query, uom_list)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

    def delete_all(self):
        """
        Deletes everything from uom_table using TRUNCATE
        """
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        try:
            with conn.cursor() as cursor:
                query = "TRUNCATE TABLE uom_table;"
                cursor.execute(query)
                conn.commit()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
            conn.rollback()
        finally:
            conn.close()

    def get_multiplier(self, uno, uline):
        """
        Return the multiplier, default is 1
        :param uno: job number
        :param uline: line number
        :return: multiplier from uom_table, returns 1 for not line 1 & 1 for not found
        """
        if uline != 1:
            return 1

        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                query = "SELECT IFNULL( (SELECT uom_table.multiplier FROM uom_table LEFT JOIN jobs_table " \
                        "ON uom_table.ustk = jobs_table.ustk WHERE uno=%s AND uline=%s LIMIT 1), 1)"
                cursor.execute(query, (uno, uline))
                multiplier = cursor.fetchone()
        except pymysql.DatabaseError as error:
            self.logger.error("{}: {}".format(sys._getframe().f_code.co_name, error))
        finally:
            conn.close()
            return multiplier
