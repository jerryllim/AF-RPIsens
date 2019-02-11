import pymysql
from datetime import datetime, timedelta


class DatabaseServer:
	def __init__(self, host='localhost', user='user', password='pass', db='test'):
		self.host = host
		self.user = user
		self.password = password
		self.db = db

		self.create_jam_table()

	def setting_json(self):
		# TODO create dictionary based on server settings

		sett_dict = {
			"machine": "Kruger",
			"IP": "152.228.1.124:9999",
			"S01": ("Kruger", "output"),
			"S02": ("Kruger", "col2"),
			"S03": ("Kruger", "col3"),
			"S04": None,
			"S05": ("Kruger", "col5"),
			"S06": None,
			"S07": ("Kruger", "col7"),
			"S08": ("Kruger", "col8"),
			"S09": None,
			"S10": ("Kruger", "col10"),
			"S11": None,
			"S12": None,
			"S13": None,
			"S14": None,
			"S15": None,
			"E01": None,
			"E02": None,
			"E03": None,
			"E04": None,
			"E05": None
		}

		return sett_dict

	def receive_match(self):
		# TODO retrieve json from RPi and match with settings_json
		recv_dict = {
			'A0001_Z00012345001_1459': {'S01': 100, 'S02': 125, 'S10': 1},
			'A0001_Z00012345001_1500': {'S01': 25, 'S02': 30, 'S10': 0}
		}
		sett_dict = self.setting_json()
		for recv_id, recv_info in recv_dict.items():
			for key in recv_info:
				if sett_dict.get(key, None):
					print(key, " ", sett_dict[key])

				else:
					print(key, " not found")

	def create_jam_table(self):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				# Drop table if it already exist (for testing)
				cursor.execute("DROP TABLE IF EXISTS jam_current_table;")

				# create JAM table
				# TODO confirm varchar lengths
				sql = '''CREATE TABLE IF NOT EXISTS jam_current_table (
						machine VARCHAR(10) NOT NULL,
						jo_no INTEGER NOT NULL,
						emp VARCHAR(10) NOT NULL
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
						PRIMARY KEY(machine, jo_no, date_time));'''

				cursor.execute(sql)
				db.commit()
		except pymysql.MySQLError:
			db.rollback()
		finally:
			db.close()

	def insert_jam(self):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				recv_dict = {
					'A0001_Z00012345001_1459': {'S01': 100, 'S02': 125, 'S10': 1},
					'A0001_Z00012345001_1500': {'S01': 25, 'S02': 30, 'S10': 0}
				}
				sett_dict = self.setting_json()
				for recv_id, recv_info in recv_dict.items():

					emp, job, time = recv_id.split('_', 3)
					recv_time = datetime.strptime(time, '%H%M')
					now = datetime.now()
					date_time = now.replace(hour=recv_time.hour, minute=recv_time.minute)
					if recv_time.time() > now.time():
						date_time = date_time - timedelta(1)

					for key in recv_info.keys():

						values = sett_dict.get(key, None)

						if values:
							query = """INSERT INTO jam_current_table (machine, jo_no, emp, datetime, {header}) VALUES 
										({machine}, {jo_no}, {emp}, {date_time}, {value} ON DUPLICATE KEY UPDATE 
										{header} = {header} + {value}""".format(header=values[1],
																				machine=values[0],
																				jo_no=job, emp=emp,
																				date_time=date_time,
																				value=recv_info[key])
							cursor.execute(query)
				db.commit()
		except pymysql.MySQLError:
			db.rollback()
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
				sql = '''CREATE TABLE IF NOT EXISTS job_info_table (
						jo_no VARCHAR(13) PRIMARY KEY,
						mac VARCHAR(5),
						to_do INT,
						code VARCHAR(14),
						descp VARCHAR(50),
						so_no VARCHAR(30),
						edd VARCHAR(12),
						so_qty INT,
						so_rem VARCHAR(10),
						ran INT'''
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
		column_names = ['jo_no', 'mac', 'to_do', 'code', 'descp', 'so_no', 'edd', 'so_qty', 'so_rem']
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

	def update_job(self, ran_no, jo_id):
		db = pymysql.connect(self.host, self.user, self.password, self.db)
		try:
			with db.cursor() as cursor:
				sql = '''UPDATE job_info SET ran = %s WHERE jo_no = %s'''
				cursor.execute(sql, (ran_no, jo_id,))
				self.check_complete(cursor, jo_id)  # Check if job has been completed
				db.commit()
		except pymysql.MySQLError as error:
			print("Failed to update record to database: {}".format(error))
		finally:
			db.close()

	def delete_job(self, jo_ids):
		"""
		Delete multiple jobs
		:param jo_ids: List of jo_id
		:return:
		"""
		db = pymysql.connect(self.host, self.user, self.password, self.db)
		try:
			with db.cursor() as cursor:
				query = '''DELETE FROM job_info WHERE jo_no = %s'''
				cursor.executemany(query, jo_ids)
		except pymysql.MySQLError as error:
			print("Failed to update record to database: {}".format(error))
		finally:
			db.close()

	@staticmethod
	def check_complete(cursor, jo_id):
		query = '''DELETE FROM job_info WHERE jo_no = %s AND ran >= to_do'''
		cursor.execute(query, jo_id)

	def create_qc_table(self):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				# TODO check varchar length for emp, machine & jo_no columns
				query = '''CREATE TABLE IF NOT EXISTS qc_table (
						emp_id VARCHAR(10) NOT NULL,
						date_time DATETIME NOT NULL,
						machine VARCHAR(10) NOT NULL,
						jo_no VARCHAR(10) NOT NULL,
						quality TINYINT UNSIGNED NOT NULL);'''
				cursor.execute(query)
				db.commit()
		finally:
			db.close()

	def insert_qc(self, values):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				for value in values:
					query = '''INSERT INTO qc_table (emp_id, date_time, machine, jo_no, quality) 
							VALUES (%s, %s, %s, %s, %s)'''
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
				query = '''CREATE TABLE IF NOT EXISTS maintenance_table (
						emp_id VARCHAR(10) NOT NULL,
						start_time DATETIME NOT NULL,
						end_time DATETIME NOT NULL,
						machine VARCHAR(10) NOT NULL;'''
				cursor.execute(query)
				db.commit()
		finally:
			db.close()

	def insert_maintenance(self, values):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				for value in values:
					query = '''INSERT INTO maintenance_table (emp_id, start_time, end_time, machine) 
							VALUES (%s, %s, %s, %s)'''
					cursor.execute(query, value)

				db.commit()
		finally:
			db.close()

	def create_ink_key_table(self):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				# Drop table if it already exist
				cursor.execute("DROP TABLE IF EXISTS ink_key_table;")
				cursor.execute("DROP TABLE IF EXISTS ink_impression_table;")

				# TODO check varchar length for item 14? & plate 13?.
				query = '''CREATE TABLE IF NOT EXISTS ink_key_table (
						item VARCHAR(20) NOT NULL,
						plate VARCHAR(20) NOT NULL,
						`1` SMALLINT UNSIGNED,
						`2` SMALLINT UNSIGNED,
						`3` SMALLINT UNSIGNED,
						`4` SMALLINT UNSIGNED,
						`5` SMALLINT UNSIGNED,
						`6` SMALLINT UNSIGNED,
						`7` SMALLINT UNSIGNED,
						`8` SMALLINT UNSIGNED,
						`9` SMALLINT UNSIGNED,
						`10` SMALLINT UNSIGNED,
						`11` SMALLINT UNSIGNED,
						`12` SMALLINT UNSIGNED,
						`13` SMALLINT UNSIGNED,
						`14` SMALLINT UNSIGNED,
						`15` SMALLINT UNSIGNED,
						`16` SMALLINT UNSIGNED,
						`17` SMALLINT UNSIGNED,
						`18` SMALLINT UNSIGNED,
						`19` SMALLINT UNSIGNED,
						`20` SMALLINT UNSIGNED,
						`21` SMALLINT UNSIGNED,
						`22` SMALLINT UNSIGNED,
						`23` SMALLINT UNSIGNED,
						`24` SMALLINT UNSIGNED,
						`25` SMALLINT UNSIGNED,
						`26` SMALLINT UNSIGNED,
						`27` SMALLINT UNSIGNED,
						`28` SMALLINT UNSIGNED,
						`29` SMALLINT UNSIGNED,
						`30` SMALLINT UNSIGNED,
						`31` SMALLINT UNSIGNED,
						`32` SMALLINT UNSIGNED,
						PRIMARY KEY(item, plate));'''
				cursor.execute(query)

				query2 = '''CREATE TABLE IF NOT EXISTS ink_impression_table (
						item VARCHAR(20) PRIMARY KEY,
						impression SMALLINT UNSIGNED NOT NULL);'''
				cursor.execute(query2)
				db.commit()
		finally:
			db.close()

	def replace_ink_key(self, ink_keys):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			with db.cursor() as cursor:
				for item, info in ink_keys.items():
					impression = info.pop('impression')
					query = '''REPLACE INTO ink_impression_table (item, impression) VALUES (%s, %s)'''
					cursor.execute(query, (item, impression))

					for plate, i_keys in info.items():
						keys = ",".join("'{}'".format(k) for k in range(1, len(i_keys)+1))
						p_s = ",".join(list('%s'*len(i_keys)))
						values = [item, plate] + i_keys
						query2 = 'REPLACE INTO ink_key_table (item,plate,' + keys + ') VALUES (%s,%s,' + p_s + ');'
						cursor.execute(query2, values)

			db.commit()
		finally:
			db.close()

	def get_ink_key(self, item):
		db = pymysql.connect(self.host, self.user, self.password, self.db)

		try:
			d = {}
			with db.cursor() as cursor:
				query = "SELECT impression FROM ink_impression_table WHERE item = %s LIMIT 1"
				cursor.execute(query, (item,))
				impression = cursor.fetchone()
				if impression:
					d['impression'] = impression

				query2 = "SELECT * FROM ink_key_table WHERE item = %s"
				cursor.execute(query2, (item,))
				for row in cursor:
					plate = row[1]
					new = [v for v in list(row) if type(v) == int]

					d[plate] = new

			db.commit()
		finally:
			db.close()
			return d


if __name__ == '__main__':
	DatabaseServer()
