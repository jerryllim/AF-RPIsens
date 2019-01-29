import pymysql

class DatabaseServer:
	def __init__(self):
		self.insert_JAM()

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
			'Z00012345_A0001_1459':{'S01':100,'S02':125,'S10':1},
			'Z00012345_A0001_1500':{'S01':25,'S02':30,'S10':0}
		}
		sett_dict = self.setting_json()
		for recv_id, recv_info in recv_dict.items():
			for key in recv_info:
				if sett_dict.get(key, None):
					print(key, " ", sett_dict[key])

				else:
					print(key, " not found")

	def create_JAM(self):
		db = pymysql.connect("localhost", "user", "pass", "test")
		cursor = db.cursor()
		try:
			# Drop table if it already exist
			cursor.execute("DROP TABLE IF EXISTS jam;")

			# create JAM table
			sql = '''CREATE TABLE IF NOT EXISTS jam (
					machine VARCHAR(10) NOT NULL,
					jo_no INTEGER NOT NULL,
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
		finally:
			db.close()

	"""def insert_JAM(self):
		db = pymysql.connect("localhost", "user", "pass", "test")
		cursor = db.cursor()
		try:
			# Insert value into table
			sql = '''INSERT INTO jam (machine, jo_no, date_time, output, col1, col2, col3, col4, col5, col5, col6, col7, col8, col9, col10)
					VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'''
			cursor.execute(sql, (sens["sensor"], sens["data"], sens["client"]))
			db.commit()
		finally:
			db.close()"""

	def insert_JAM(self):
		db = pymysql.connect("localhost", "user", "pass", "test")

		try:
			with db.cursor() as cursor:
				column_names = ['machine', 'jo_no', 'date_time', 'output', 'col1', 'col2', 'col3', 'col4', 'col5', 'col5', 'col6', 'col7', 'col8', 'col9', 'col10']
				column_names_str = ', '.join(column_names)
				binds_str = ', '.join('%s' for _ in range(len(column_names)))
				recv_dict = {
					'Z00012345_A0001_1459':{'S01':100,'S02':125,'S10':1},
					'Z00012345_A0001_1500':{'S01':25,'S02':30,'S10':0}
				}
				sett_dict = self.setting_json()
				for recv_id, recv_info in recv_dict.items():
					for key in recv_info:
						if sett_dict.get(key, None):
							sql = ("INSERT INTO jam ({column_names}) "
									"VALUES ({binds})"
									.format(column_names=column_names_str,
									binds=binds_str))
							values = [recv_info[column_name] for column_name in column_names]
							cursor.execute(sql, values)
							print("Inserted successfully")
				db.commit()
		finally:
			db.close()
			
	def create_emp(self):
		db = pymysql.connect("localhost", "user", "pass", "test")
		cursor = db.cursor()
		try:
			# Drop table if it already exist
			cursor.execute("DROP TABLE IF EXISTS emp;")

			# create EMP table
			sql = '''CREATE TABLE IF NOT EXISTS emp (
					emp_no VARCHAR(10) NOT NULL PRIMARY KEY,
					name VARCHAR(20),
					modified DATETIME)'''

			cursor.execute(sql)
			db.commit()
		finally:
			db.close()

	def insert_emp(self):
		db = pymysql.connect("localhost", "user", "pass", "test")
		cursor = db.cursor()
		try:
			sql = '''INSERT INTO emp (emp_no, name, modified)
					VALUES (%s, %s, %s);'''
			cursor.execute(sql, (self.emp_no.get(), self.emp_name.get(), time.strftime('%Y-%m-%d %H:%M:%S')))
			db.commit()
			self.insert_temp(emp_no, name)
		except MySQLError as error:
			print("Failed to insert record to database: {}".format(error))
			db.rollback()
		finally:
			db.close()

	def delete_emp(self):
		db = pymysql.connect("localhost", "user", "pass", "test")
		cursor = db.cursor()
		try:
			sql = '''DELETE FROM emp WHERE emp_no = %s'''
			cursor.execute(sql, (self.emp_no.get()))
			db.commit()
			self.insert_temp(emp_no)
		except MySQLError as error:
			print("Failed to delete record from database: {}".format(error))
			db.rollback()
		finally:
			db.close()

	def update_emp(self):
		db = pymysql.connect("localhost", "user", "pass", "test")
		cursor = db.cursor()
		try:
			sql = '''UPDATE emp SET name = %s, modified = %s WHERE emp_no = %s'''
			cursor.execute(sql, (self.emp_name.get(), time.strftime('%Y-%m-%d %H:%M:%S')))
			db.commit()
			self.insert_temp(emp_no, name)
		except MySQLError as error:
			print("Failed to update record to database: {}".format(error))
			db.rollback()
		finally:
			db.close()

	def t_emp(self):
		db = pymysql.connect("localhost", "user", "pass", "test")
		cursor = db.cursor()
		try:
			# create temp EMP table
			sql = '''CREATE TABLE IF NOT EXISTS t_emp (
					emp_no VARCHAR(10) NOT NULL PRIMARY KEY,
					name VARCHAR(20),
					modified DATETIME)'''
			cursor.execute(sql)
			db.commit()
		except MySQLError as error:
			print("Failed to create table in database: {}".format(error))
			db.rollback()
		finally:
			db.close()

	def insert_temp(self, emp_no, name = None):
		self.t_emp()
		db = pymysql.connect("localhost", "user", "pass", "test")
		cursor = db.cursor()
		try:
			sql = '''INSERT INTO t_emp (emp_no, name, modified)
					VALUES (%s, %s, %s)
					ON DUPLICATE KEY UPDATE emp_no = %s, name = %s, modified = %s'''
			cursor.execute(sql, (emp_no, name, time.strftime('%Y-%m-%d %H:%M:%S'), emp_no, name, time.strftime('%Y-%m-%d %H:%M:%S')))
			db.commit()
		except MySQLError as error:
			print("Failed to insert/update record to database: {}".format(error))
			db.rollback()
		finally:
			db.close()


if __name__ == '__main__':
	DatabaseServer()
