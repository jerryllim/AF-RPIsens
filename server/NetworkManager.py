import zmq
import json
import time
import pymysql
import threading
import databaseServer
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler

class NetworkManager:
	dealer = None
	router = None
	port_numbers = ["152.228.1.135:7777", ]
	# port_number = "{}:8888".format(self.self_add)

	def __init__(self):
		self.context = zmq.Context()
		self.settings = databaseServer.Settings()
		self.database_manager = databaseServer.DatabaseManager(self.settings)
		self.router_routine()
		self.dealer_routine()
		self.router_thread = threading.Thread(target=self.route)
		self.router_thread.daemon = True
		self.router_thread.start()

	def dealer_routine(self):
		self.dealer = self.context.socket(zmq.DEALER)
		self.dealer.setsockopt(zmq.LINGER, 0)

	def request(self, port, msg):
		temp_list = {}
		self.dealer.connect("tcp://%s" % port)
		print(port)
		msg_json = json.dumps(msg)
		self.dealer.send_string("", zmq.SNDMORE)  # delimiter
		self.dealer.send_string(msg_json)
		print("request msg sent")

		# use poll for timeouts:
		poller = zmq.Poller()
		poller.register(self.dealer, zmq.POLLIN)

		socks = dict(poller.poll(5 * 1000))

		if self.dealer in socks:
			try:
				self.dealer.recv() # delimiter
				recv_msg = self.dealer.recv_json()
				print(recv_msg)
				temp_list.update(recv_msg)
			except IOError as error:
				print("Problem with socket: ", error)
			finally:
				self.dealer.disconnect("tcp://%s" % port)
		else:
			print("Machine is not connected")

		return temp_list			

	def router_routine(self):
		# port_number = "{}:9999".format(self.self_add)
		port_number = "152.228.1.124:9999"
		self.router = self.context.socket(zmq.ROUTER)
		self.router.bind("tcp://%s" % port_number)
		# print("Successfully binded to port %s for respondent" % self.port_number)

	def route(self):
		while True:
			ident = self.router.recv()  # routing information
			delimiter = self.router.recv()  # delimiter
			message = self.router.recv_json()
			reply_dict = {}

			for key in message.keys():
				if key == "job_info":
					barcode = message.get("job_info", None)
					reply_dict = self.database_manager.get_job_info(barcode)
				elif key == "sfu":
					pass
				elif key == "ink_key":
					ink_key = message.get("ink_key", None)
					self.database_manager.replace_ink_key(ink_key)

			self.router.send(ident, zmq.SNDMORE)
			self.router.send(delimiter, zmq.SNDMORE)
			self.router.send_json(reply_dict)

	def request_jam(self):
		for port in self.port_numbers:
			msg_dict = {"jam": None}
			deal_msg = self.request(port, msg_dict)

			machine_ip = deal_msg.get('ip')
			machine = self.settings.get_machine(machine_ip)

			jam_msg = deal_msg.pop('jam', {})
			qc_list = deal_msg.pop('qc', [])

			if qc_list:
				self.database_manager.insert_qc(machine, qc_list)

			maintenance_list = jam_msg.pop('qc', [])
			if maintenance_list:
				self.database_manager.insert_maintenance(machine, maintenance_list)

			self.database_manager.insert_jam(machine_ip, jam_msg)

	def send_job_info(self):
		# TODO retrive mac from server settings
		for ip in self.settings.get_ips():
			mac = self.settings.get_mac(ip)
			job_list = self.database_manager.get_jobs_for(mac)
			self.request({'job_info': job_list})

	def send_ink_key(self):
		# TODO retrieve machine from server settings
		for ip in self.settings.get_ips():
			machine = self.settings.get_machine(ip)
			msg_dict = self.database_manager.get_ink_key(machine)
			self.request(msg_dict)

	def send_emp(self):
		msg_dict = self.database_manager.get_emp()
		self.request(msg_dict)

	def request_schedule(self, interval=5):
		# TODO create self.scheduler instead? So that the schedule can be changeable, to remove all jobs at change?
		scheduler = BackgroundScheduler()
		cron_trigger = CronTrigger(minute='*/{}'.format(interval))
		# TODO change id as a constant string instead of harcoded?
		self.job = scheduler.add_job(self.request_jam, cron_trigger, id='5mins')
		# TODO do a self.scheduler.start() outside of this function?
		scheduler.start()


if __name__ == '__main__':
	NetworkManager()
