import pymysql
from datetime import datetime, timedelta


class Settings:
	setting = {"152.228.1.135": {
			"machine": "Exia",
			"mac": 'ZF1',
			"S01": None,
			"S02": ("Exia", "col2"),
			"S03": ("Exia", "col3"),
			"S04": None,
			"S05": ("Exia", "col5"),
			"S06": None,
			"S07": ("Exia", "col7"),
			"S08": ("Exia", "col8"),
			"S09": None,
			"S10": ("Exia", "col10"),
			"S11": None,
			"S12": None,
			"S13": None,
			"S14": None,
			"S15": ("Exia", "output"),
			"E01": ("Exia", "col1"),
			"E02": None,
			"E03": None,
			"E04": None,
			"E05": None},
		"152.228.1.192": {
		"machine": "SM53",
		"mac": 'ZP10',
		"S01": None,
		"S02": None,
		"S03": None,
		"S04": None,
		"S05": ("SM53", "col5"),
		"S06": None,
		"S07": ("SM53", "col7"),
		"S08": ("SM53", "col8"),
		"S09": None,
		"S10": ("SM53", "col10"),
		"S11": None,
		"S12": None,
		"S13": None,
		"S14": None,
		"S15": ("SM53", "output"),
		"E01": ("SM53", "col1"),
		"E02": ("SM53", "col2"),
		"E03": ("SM53", "col3"),
		"E04": None,
		"E05": None}}

	def get_ip_key(self, ip, key):
		print("in class settings: ", self.setting[ip][key])
		if self.setting.get(ip) and (self.setting.get(ip)).get(key):
			return self.setting[ip][key]
		else:
			return None

	def get_mac(self, ip):
		if self.setting.get(ip):
			return self.setting[ip]['mac']
		else:
			return False

	def get_machine(self, ip):
		if self.setting.get(ip):
			return self.setting[ip]['machine']
		else:
			return False

	def get_ips(self):
		return list(self.setting.keys())


class DatabaseManager:
	def __init__(self, settings, host='localhost', user='user', password='pass', db='test'):
		self.settings = settings
		self.host = host
		self.user = user
		self.password = password
		self.db = db
		# localhost, user, pass, test

		self.create_jam_table()
		self.create_job_table()

	def create_jam_table(self):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				# Drop table if it already exist (for testing)
				# cursor.execute("DROP TABLE IF EXISTS jam_current_table;")

				# create JAM table
				# TODO confirm varchar lengths
				sql = '''CREATE TABLE IF NOT EXISTS jam_current_table (
						machine VARCHAR(10) NOT NULL,
						jo_no VARCHAR(15) NOT NULL,
						emp VARCHAR(10) NOT NULL,
						date_time DATETIME NOT NULL,
						output INTEGER DEFAULT 0,
						col1 INTEGER DEFAULT 0,
						col2 INTEGER DEFAULT 0,
						col3 INTEGER DEFAULT 0,
						col4 INTEGER DEFAULT 0,
						col5 INTEGER DEFAULT 0,
						col6 INTEGER DEFAULT 0,
						col7 INTEGER DEFAULT 0,
						col8 INTEGER DEFAULT 0,
						col9 INTEGER DEFAULT 0,
						col10 INTEGER DEFAULT 0,
						PRIMARY KEY(machine, jo_no, date_time, emp));'''

				cursor.execute(sql)

				db.commit()
		except pymysql.MySQLError:
			db.rollback()
		finally:
			db.close()

	def insert_jam(self, ip, recv_dict=None):
		# TODO remove recv_dict as a keyword argument
		# if not recv_dict:
		# 	recv_dict = {
		# 		'A0001_Z00012345001_1459': {'S01': 100, 'S02': 125, 'S10': 1},
		# 		'A0001_Z00012345001_1500': {'S01': 25, 'S02': 30, 'S10': 0}
		# 	}

		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				# TODO change sett_dict format
				# sett_dict = self.setting_json()
				for recv_id, recv_info in recv_dict.items():
					print(recv_id)  # TODO to delete this print?
					emp, job, time_str = recv_id.split('_', 3)
					recv_time = datetime.strptime(time_str, '%H%M')
					now = datetime.now()
					date_time = now.replace(hour=recv_time.hour, minute=recv_time.minute)
					if recv_time.time() > now.time():
						date_time = date_time - timedelta(1)

					for key in recv_info.keys():
						# values = sett_dict.get(key, None)
						values = self.settings.get_ip_key(ip, key)
						# print(values)

						if values:
							query = "INSERT INTO jam_current_table (machine, jo_no, emp, date_time, "\
							"{header}) VALUES ('{machine}', '{jo_no}', '{emp}', '{date_time}', {value}) ON "\
							"DUPLICATE KEY UPDATE {header} = {header} + {value};".format(header=values[1],
														     machine=values[0],
														     jo_no=job, emp=emp,
														     date_time=date_time.strftime("%Y-%m-%d %H:%M"),
														     value=recv_info[key])
							cursor.execute(query)
				db.commit()
		except pymysql.MySQLError as error:
			db.rollback()
			print("Failed to insert record to database: {}".format(error))
		finally:
			db.close()

	def create_emp_table(self):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				# Drop table if it already exist
				cursor.execute("DROP TABLE IF EXISTS emp_table;")

				# create EMP table
				sql = '''CREATE TABLE IF NOT EXISTS emp_table (
						emp_no VARCHAR(10) PRIMARY KEY,
						name VARCHAR(40),
						last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)'''

				cursor.execute(sql)
				db.commit()
		finally:
			db.close()

	def insert_emp(self, emp_id, emp_name):
		db = pymysql.connect(self.host, self.user, self.password, self.db)
		try:
			with db.cursor() as cursor:
				sql = '''INSERT INTO emp_table (emp_no, name) VALUES (%s, %s);'''
				cursor.execute(sql, (emp_id, emp_name))
				db.commit()
				self.insert_t_emp(emp_id, emp_name)

		except pymysql.MySQLError as error:
			print("Failed to insert record to database: {}".format(error))
			db.rollback()
		finally:
			db.close()

	def delete_emp(self, emp_id):
		db = pymysql.connect(self.host, self.user, self.password, self.db)
		try:
			with db.cursor() as cursor:
				sql = '''DELETE FROM emp_table WHERE emp_no = %s'''
				cursor.execute(sql, (emp_id,))
				db.commit()
				self.insert_t_emp(emp_id)

		except pymysql.MySQLError as error:
			print("Failed to delete record from database: {}".format(error))
			db.rollback()
		finally:
			db.close()

	def update_emp(self, emp_id, emp_name):
		db = pymysql.connect(self.host, self.user, self.password, self.db)
		try:
			with db.cursor() as cursor:
				sql = '''UPDATE emp_table SET name = %s WHERE emp_no = %s'''
				cursor.execute(sql, (emp_name, emp_id))
				db.commit()
				self.insert_t_emp(emp_id, emp_name)

		except pymysql.MySQLError as error:
			print("Failed to update record to database: {}".format(error))
			db.rollback()
		finally:
			db.close()
			
	def get_emp(self):
		db = pymysql.connect(self.host, self.user, self.password, self.db)
		reply_dict = {}
		cursor = db.cursor(pymysql.cursors.DictCursor)

		try:
			sql = '''SELECT * FROM emp_table'''
			cursor.execute(sql)
			reply_dict = cursor.fetchall()
			db.commit()
		except pymysql.MySQLError as error:
			print("Failed to select record in database: {}".format(error))
		finally:
			db.close()
			return reply_dict

	def create_t_emp_table(self):
		db = pymysql.connect(self.host, self.user, self.password, self.db)
		try:
			with db.cursor() as cursor:
				# create temp EMP table
				sql = '''CREATE TABLE IF NOT EXISTS t_emp_table (
						emp_no VARCHAR(10) PRIMARY KEY,
						name VARCHAR(40),
						last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)'''
				cursor.execute(sql)
				db.commit()

		except pymysql.MySQLError as error:
			print("Failed to create table in database: {}".format(error))
			db.rollback()
		finally:
			db.close()

	def insert_t_emp(self, emp_id, emp_name=None):
		self.create_t_emp_table()
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				sql = '''INSERT INTO t_emp (emp_no, name,) VALUES (%s, %s)
						ON DUPLICATE KEY UPDATE name = %s'''
				cursor.execute(sql, (emp_id, emp_name, emp_name))
				db.commit()

		except pymysql.MySQLError as error:
			print("Failed to insert/update record to database: {}".format(error))
			db.rollback()
		finally:
			db.close()

	def create_job_table(self):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				# Drop table if it already exist
				cursor.execute("DROP TABLE IF EXISTS job_info_table;")

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

				print(sql)
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
		db = pymysql.connect(self.host, self.user, self.password, self.db)

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
		db = pymysql.connect(self.host, self.user, self.password, self.db)

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
						'start TINYINT NOT NULL;'
				cursor.execute(query)
				db.commit()
		finally:
			db.close()

	def insert_maintenance(self, machine, values):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

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
