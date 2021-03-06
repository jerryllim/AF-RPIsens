import sys
import time
import serverNetwork
import serverDatabase
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler

settings_ = serverDatabase.Settings()
db_manager = serverDatabase.DatabaseManager(settings_, user='user', password='pass', db='test')
network_manager = serverNetwork.NetworkManager(settings_, db_manager)

try:
	while True:
		jam = input("\noption 1: jam\noption 2: jam every 5 mins\noption 3: exit\nplease enter the option no.\n")
		if jam == "1":
			network_manager.request_jam()

		elif jam == "2":
			now = time.strftime("%Y-%m-%d %H:%M:%S")
			print("requesting every 5 mins... %s" % now)
			scheduler = BackgroundScheduler()
			cron_trigger = CronTrigger(minute='*/5')
			job = scheduler.add_job(network_manager.request_jam, cron_trigger, id='5mins', misfire_grace_time=30,
									max_instances=3)
			scheduler.start()

		elif jam == "3":
			now = time.strftime("%Y-%m-%d %H:%M:%S")
			print("exiting... %s" % now)
			break

		else:
			print("no such commands")

except KeyboardInterrupt:
	print("interrupted with ctrl+c")
	raise
# finally:
	# sys.exit()