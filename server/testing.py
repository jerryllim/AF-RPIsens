import sys
import time
import NetworkManager
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler

network_manager = NetworkManager.NetworkManager()
now = time.strftime("%Y-%m-%d %H:%M:%S")

try:
	while True:
		jam = input("\noption 1: jam\noption 2: jam every 5 mins\noption 3: exit\nplease enter the option no.\n")
		if jam == "1":
			print("requesting... %s" % now)

			network_manager.request_jam()

		elif jam == "2":
			print("requesting every 5 mins... %s" % now)
			scheduler = BackgroundScheduler()
			cron_trigger = CronTrigger(minute='*/5')
			job = scheduler.add_job(network_manager.request_jam, cron_trigger, id = '5mins', misfire_grace_time=30, max_instances=3)
			scheduler.start()

		elif jam == "3":
			print("exiting... %s" % now)
			break

		else:
			print("no such commands")

except KeyboardInterrupt:
	print("interrupted with ctrl+c")
	raise
# finally:
	# sys.exit()