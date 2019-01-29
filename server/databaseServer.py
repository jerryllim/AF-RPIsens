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


if __name__ == '__main__':
	DatabaseServer()