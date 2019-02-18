import sys
import NetworkManager
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler

network_manager = NetworkManager.NetworkManager()

try:
	while True:
		jam = input("\noption 1: jam\noption 2: jam every 5 mins\noption 3: exit\nplease enter the option no.\n")
		if jam == "1":
			print("requesting...")

			network_manager.request_jam()

		elif jam == "2":
			print("requesting every 5 mins...")
			scheduler = BackgroundScheduler()
			cron_trigger = CronTrigger(minute='*/5')
			job = scheduler.add_job(network_manager.request_jam, cron_trigger, id = '5mins')
			scheduler.start()

		elif jam == "3":
			print("exiting...")
			break
			
		else:
			print("no such commands")

except KeyboardInterrupt:
	print("interrupted with ctrl+c")
	raise
# finally:
	# sys.exit()