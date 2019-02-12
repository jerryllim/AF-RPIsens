import zmq
import json
import time
import pymysql
import threading
from server import databaseServer
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler


class NetworkManager:
	dealer = None
	router = None
	port_numbers = ["152.228.1.124:8888", "152.228.1.124:7777"]
	# port_number = "{}:8888".format(self.self_add)

	def __init__(self):
		self.context = zmq.Context()
		self.database_manager = databaseServer.DatabaseManager()
		self.dealer_routine()
		self.router_routine()

	def dealer_routine(self):
		self.dealer = self.context.socket(zmq.DEALER)
		self.dealer.setsockopt(zmq.LINGER, 0)
		for port in port_numbers:
			self.dealer.connect("tcp://%s" % port)
			#print("Successfully connected to machine %s" % port_number)

	def request(self, msg):
		for port in port_numbers:
			msg_json = json.dumps(msg)
			self.dealer.send_string("", zmq.SNDMORE)  # delimiter
			self.dealer.send_string(msg_json)
			print("request msg sent")

			# use poll for timeouts:
			poller = zmq.Poller()
			poller.register(self.dealer, zmq.POLLIN)

			socks = dict(poller.poll(3 * 1000))

			if self.dealer in socks:
				try:
					recv_msg = self.dealer.recv_string()
					# print("recv_msg: %s" % recv_msg)
					deal_msg = json.loads(recv_msg)
					return deal_msg
				except IOError as error:
					print("Problem with socket")
			else:
				print("Machine did not respond")			

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
		msg_dict = {}
		deal_msg = self.request(msg_dict)

		self.database_manager.insert_jam(deal_msg)

	def send_job_info(self):
		# TODO retrive mac from server settings
		msg_dict = self.database_manager.get_spec_job(mac)
		self.request(msg_dict)

	def send_ink_key(self):
		# TODO retrieve machine from server settings
		msg_dict = self.database_manager.get_ink_key(item, machine)
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
