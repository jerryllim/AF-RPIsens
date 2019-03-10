import pymysql
import configparser
from datetime import datetime, timedelta


class Settings:
    def __init__(self, filename='jam.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(filename)
        self.machine_info = {}

    def get_machine_info(self):
        database_manager = DatabaseManager(None)

    def get_ip_key(self, ip, key):
        print("in class settings: ", self.machine_info[ip][key])
        if self.machine_info.get(ip) and (self.machine_info.get(ip)).get(key):
            return self.machine_info[ip][key]
        else:
            return None

    def get_mac(self, ip):
        if self.machine_info.get(ip):
            return self.machine_info[ip]['mac']
        else:
            return False

    def get_machine(self, ip):
        if self.machine_info.get(ip):
            return self.machine_info[ip]['nickname']
        else:
            return False

    def get_ips(self):
        return list(self.machine_info.keys())


class DatabaseManager:
    def __init__(self, settings, host='', user='', password='', db='', port=''):
        self.settings = settings
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        if port.isnumeric():
            port = int(port)
        self.port = port

        self.create_jam_table()
        self.create_job_table()
        self.create_emp_table()
        self.create_maintenance_table()
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
            print(error)

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
            conn.rollback()
            print(error)
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
                # TODO confirm varchar lengths
                sql = '''CREATE TABLE IF NOT EXISTS jam_current_table (
                machine VARCHAR(10) NOT NULL,
                jo_no VARCHAR(15) NOT NULL,
                emp VARCHAR(10) NOT NULL,
                date_time DATETIME NOT NULL,
                shift TINYINT(1) UNSIGNED DEFAULT 0,
                output INT UNSIGNED DEFAULT 0,
                col1 INT DEFAULT 0,
                col2 INT DEFAULT 0,
                col3 INT DEFAULT 0,
                col4 INT DEFAULT 0,
                col5 INT DEFAULT 0,
                col6 INT DEFAULT 0,
                col7 INT DEFAULT 0,
                col8 INT DEFAULT 0,
                col9 INTEGER DEFAULT 0,
                col10 INT DEFAULT 0,
                PRIMARY KEY(machine, jo_no, date_time, emp));'''

                cursor.execute(sql)

                cursor.execute('CREATE TABLE IF NOT EXIST jam_prev_table LIKE jam_current_table;')
                cursor.execute('CREATE TABLE IF NOT EXIST jam_past_table LIKE jam_current_table;')

                conn.commit()
        except pymysql.MySQLError:
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
            conn.rollback()
            print("Failed to insert record to database: {}".format(error))
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
            conn.rollback()
            print("Failed to insert record to database: {}".format(error))
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
        finally:
            conn.close()

    def create_emp_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                # TODO check length of the emp_id and name
                # create EMP table
                sql = '''CREATE TABLE IF NOT EXISTS emp_table (
                emp_id VARCHAR(10) PRIMARY KEY,
                name VARCHAR(40),
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                to_del TINYINT(1))'''

                cursor.execute(sql)
                conn.commit()
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
            conn.rollback()
            print("Failed to insert record to database: {}".format(error))
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
            conn.rollback()
            print("Failed to insert record to database: {}".format(error))
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
            print("Failed to mark to delete records from database: {}".format(error))
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
            print("Failed to delete records from database: {}".format(error))
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
            print("Failed to select record in database: {}".format(error))
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
            print("Failed to select record in database: {}".format(error))
        finally:
            conn.close()
            return emp_list


    # def update_emp(self, emp_id, emp_name):
    #     db = pymysql.connect(self.host, self.user, self.password, self.db)
    #     try:
    #         with db.cursor() as cursor:
    #             sql = '''UPDATE emp_table SET name = %s WHERE emp_no = %s'''
    #             cursor.execute(sql, (emp_name, emp_id))
    #             db.commit()
    #             self.insert_t_emp(emp_id, emp_name)
    #
    #     except pymysql.MySQLError as error:
    #         print("Failed to update record to database: {}".format(error))
    #         db.rollback()
    #     finally:
    #         db.close()

    # def create_t_emp_table(self):
    #     db = pymysql.connect(self.host, self.user, self.password, self.db)
    #     try:
    #         with db.cursor() as cursor:
    #             # create temp EMP table
    #             sql = '''CREATE TABLE IF NOT EXISTS t_emp_table ( emp_no VARCHAR(10) PRIMARY KEY,
    #             name VARCHAR(40),
    #             last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)'''
    #             cursor.execute(sql)
    #             db.commit()
    #
    #     except pymysql.MySQLError as error:
    #         print("Failed to create table in database: {}".format(error))
    #         db.rollback()
    #     finally:
    #         db.close()
    #
    # def insert_t_emp(self, emp_id, emp_name=None):
    #     self.create_t_emp_table()
    #     db = pymysql.connect(self.host, self.user, self.password, self.db)
    #
    #     try:
    #         with db.cursor() as cursor:
    #             sql = '''INSERT INTO t_emp (emp_no, name,) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name = %s'''
    #             cursor.execute(sql, (emp_id, emp_name, emp_name))
    #             db.commit()
    #
    #     except pymysql.MySQLError as error:
    #         print("Failed to insert/update record to database: {}".format(error))
    #         db.rollback()
    #     finally:
    #         db.close()

    def create_job_table(self):
        db = pymysql.connect(self.host, self.user, self.password, self.db)

        try:
            with db.cursor() as cursor:
                # TODO check varchar length for each column
                sql = 'CREATE TABLE IF NOT EXISTS job_info_table (' \
                      'jo_no VARCHAR(13) PRIMARY KEY,' \
                      'jo_line INT,' \
                      'mac VARCHAR(5),' \
                      'to_do INT,' \
                      'code VARCHAR(14),' \
                      'descp VARCHAR(50),' \
                      'so_no VARCHAR(30),' \
                      'edd VARCHAR(12),' \
                      'so_qty INT,' \
                      'so_rem VARCHAR(10),' \
                      'ran INT);'

                cursor.execute(sql)
                db.commit()
        finally:
            db.close()

    def insert_job(self, job_list):
        """
        Call to insert job from eb to database
        :param job_list: list containing tuples. A tuple will contain the job information e.g. ('job#', 'mac', ...,
        'so_rem')
        :return:
        """
        db = pymysql.connect(self.host, self.user, self.password, self.db)
        column_names = ['jo_no', 'jo_line', 'mac', 'to_do', 'code', 'descp', 'so_no', 'edd', 'so_qty', 'so_rem']
        column_names_str = ', '.join(column_names)
        binds_str = ', '.join(['%s'] * len(column_names))
        try:
            with db.cursor() as cursor:
                for job_info in job_list:
                    query = '''INSERT INTO job_info ({col_names}) VALUES ({binds});'''.format(col_names=column_names_str
                                                                                              , binds=binds_str)
                    cursor.execute(query, job_info)
                    db.commit()

        except pymysql.MySQLError as error:
            print("Failed to insert record to database: {}".format(error))
            db.rollback()
        finally:
            db.close()

    def update_job(self, ran_no, jo_id, jo_line):
        db = pymysql.connect(self.host, self.user, self.password, self.db)
        try:
            with db.cursor() as cursor:
                sql = '''UPDATE job_info SET ran = %s WHERE jo_no = %s AND jo_line = %s'''
                cursor.execute(sql, (ran_no, jo_id, jo_line))
                self.check_complete(cursor, jo_id, jo_line)  # Check if job has been completed
                db.commit()
        except pymysql.MySQLError as error:
            print("Failed to update record to database: {}".format(error))
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
            print("Failed to update record to database: {}".format(error))
        finally:
            db.close()

    def get_job_info(self, barcode):
        db = pymysql.connect(self.host, self.user, self.password, self.db)
        cursor = db.cursor()
        reply_dict = {}
        try:
            jo_no = barcode[:-3]
            jo_line = int(barcode[-3:])
            sql = '''SELECT code, descp, to_do, ran FROM job_info_table WHERE jo_no = %s LIMIT 1 AND jo_line = %s'''
            cursor.execute(sql, (jo_no, jo_line))
            temp = cursor.fetchone()
            reply_dict = [jo_no, jo_line] + list(temp)
            print("reply_dict: ", reply_dict)
            db.commit()
        except pymysql.MySQLError as error:
            print("Failed to select record in database: {}".format(error))
        finally:
            db.close()
            return reply_dict

    def get_jobs_for(self, mac):
        db = pymysql.connect(self.host, self.user, self.password, self.db)
        job_list = []
        try:
            with db.cursor() as cursor:
                sql = '''SELECT * FROM job_info_table WHERE mac = %s'''
                cursor.execute(sql, (mac,))
                for row in cursor:
                    job_list.append(row)

        except pymysql.MySQLError as error:
            print("Failed to select record in database: {}".format(error))
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
                query = 'CREATE TABLE IF NOT EXISTS qc_table (' \
                        'emp_id VARCHAR(10) NOT NULL,' \
                        'date_time DATETIME NOT NULL,' \
                        'machine VARCHAR(10) NOT NULL,' \
                        'jo_no VARCHAR(15) NOT NULL,' \
                        'quality TINYINT UNSIGNED NOT NULL);'
                cursor.execute(query)
                db.commit()
        finally:
            db.close()

    def insert_qc(self, machine, values):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with db.cursor() as cursor:
                for value in values:
                    emp, jo_no, time_str, grade = value
                    recv_time = datetime.strptime(time_str, '%H%M')
                    now = datetime.now()
                    date_time = now.replace(hour=recv_time.hour, minute=recv_time.minute)
                    if recv_time.time() > now.time():
                        date_time = date_time - timedelta(1)

                    query = 'INSERT INTO qc_table (emp_id, date_time, machine, jo_no, quality) VALUES ({emp}, ' \
                            '{date_time}, {machine}, {jo_no}, ' \
                            '{grade})'.format(emp=emp, date_time=date_time.strftime("%Y-%m-%d %H:%M"),
                                              machine=machine, jo_no=jo_no, grade=grade)

                    cursor.execute(query, value)

                db.commit()
        finally:
            db.close()

    def create_maintenance_table(self):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with db.cursor() as cursor:
                # Drop table if it already exist
                cursor.execute("DROP TABLE IF EXISTS maintenance_table;")

                # TODO check varchar length for emp & machine.
                query = 'CREATE TABLE IF NOT EXISTS maintenance_table (' \
                        'emp_id VARCHAR(10) NOT NULL,' \
                        'machine VARCHAR(10) NOT NULL,' \
                        'jo_no VARCHAR(15),' \
                        'date_time DATETIME NOT NULL,' \
                        'start TINYINT NOT NULL);'
                cursor.execute(query)
                db.commit()
        finally:
            db.close()

    def insert_maintenance(self, machine, values):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with db.cursor() as cursor:
                for value in values:
                    emp, jo_no, time_str, start = value
                    recv_time = datetime.strptime(time_str, '%H%M')
                    now = datetime.now()
                    date_time = now.replace(hour=recv_time.hour, minute=recv_time.minute)
                    if recv_time.time() > now.time():
                        date_time = date_time - timedelta(1)

                    query = 'INSERT INTO maintenance_table (emp_id, machine, jo_no, date_time, start) VALUES ' \
                            '({emp}, {machine}, {jo_no}, {date_time}, ' \
                            '{start})'.format(emp=emp, machine=machine, jo_no=jo_no,
                                              date_time=date_time.strftime("%Y-%m-%d %H:%M"), start=start)
                    cursor.execute(query, value)

                db.commit()
        finally:
            db.close()

    def create_pis_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = 'CREATE TABLE IF NOT EXISTS pis_table (ip VARCHAR(15) PRIMARY KEY, nick VARCHAR(15) UNIQUE, ' \
                      'mac VARCHAR(5), machineS01 VARCHAR(15), colnumS01 VARCHAR(6), machineS02 VARCHAR(15), ' \
                      'colnumS02 VARCHAR(6), machineS03 VARCHAR(15), colnumS03 VARCHAR(6), machineS04 VARCHAR(15), ' \
                      'colnumS04 VARCHAR(6), machineS05 VARCHAR(15), colnumS05 VARCHAR(6), machineS06 VARCHAR(15), ' \
                      'colnumS06 VARCHAR(6), machineS07 VARCHAR(15), colnumS07 VARCHAR(6), machineS08 VARCHAR(15), ' \
                      'colnumS08 VARCHAR(6), machineS09 VARCHAR(15), colnumS09 VARCHAR(6), machineS10 VARCHAR(15), ' \
                      'colnumS10 VARCHAR(6), machineS11 VARCHAR(15), colnumS11 VARCHAR(6), machineS12 VARCHAR(15), ' \
                      'colnumS12 VARCHAR(6), machineS13 VARCHAR(15), colnumS13 VARCHAR(6), machineS14 VARCHAR(15), ' \
                      'colnumS14 VARCHAR(6), machineS15 VARCHAR(15), colnumS15 VARCHAR(6), machineE01 VARCHAR(15), ' \
                      'colnumE01 VARCHAR(6), machineE02 VARCHAR(15), colnumE02 VARCHAR(6), machineE03 VARCHAR(15), ' \
                      'colnumE03 VARCHAR(6), machineE04 VARCHAR(15), colnumE04 VARCHAR(6), machineE05 VARCHAR(15), ' \
                      'colnumE05 VARCHAR(6));'
                cursor.execute(sql)
                conn.commit()
        finally:
            conn.close()

    def replace_pi(self, pi_row):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)
        replaced = False

        try:
            with conn.cursor() as cursor:
                sql = 'REPLACE INTO pis_table VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,' \
                      '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
                cursor.execute(sql, pi_row)
                conn.commit()
        except pymysql.MySQLError as error:
            conn.rollback()
            print(error)
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
            conn.rollback()
            print(error)
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
                    pis_dict[ip] = row
        except pymysql.MySQLError as error:
            conn.rollback()
            print(error)
        finally:
            conn.close()
            return pis_dict

    def create_machines_table(self):
        conn = pymysql.connect(host=self.host, user=self.user, password=self.password,
                               database=self.db, port=self.port)

        try:
            with conn.cursor() as cursor:
                sql = 'CREATE TABLE IF NOT EXISTS machines_table (machine VARCHAR(10) PRIMARY KEY, output INT ' \
                      'UNSIGNED, col1 INT, col2 INT, col3 INT, col4 INT, col5 INT, col6 INT, col7 INT, col8 INT, ' \
                      'col9 INT, col10 INT)'
                cursor.execute(sql)
                conn.commit()
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
            print(error)
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
            print(error)
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
            print(error)
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
            print(error)
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
            print(error)
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
            print(error)
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
            conn.rollback()
            print("Failed to insert record to database: {}".format(error))
        finally:
            conn.close()
            return targets_dict
