import zmq
import json
import time
import pymysql
import threading
import databaseServer
import apscheduler.schedulers.background

class NetworkManager:
	def __init__(self):
		self.context = zmq.Context()
		self.dealer_routine()
		self.router_routine()

	def dealer_routine(self):
		#port_number = "{}:8888".format(self.self_add)
		port_number = "152.228.1.124:8888"
		self.dealer = self.context.socket(zmq.DEALER)
		self.dealer.setsockopt(zmq.LINGER, 0)
		for port in port_number:
			self.dealer.connect("tcp://%s" % port_number)
			#print("Successfully connected to machine %s" % port_number)

	def request(self, msg):
		msg_json = json.dumps(msg)
		self.dealer.send_string("", zmq.SNDMORE)  # delimiter
		self.dealer.send_string(msg_json)
		print("request msg sent")

		# use poll for timeouts:
		poller = zmq.Poller()
		poller.register(dealer, zmq.POLLIN)

		socks = dict(poller.poll(3 * 1000))

		if self.dealer in socks:
			try:
				recv_msg = str(self.dealer.recv())
				#print("recv_msg: %s" % recv_msg)
				deal_msg = json.loads(recv_msg)
				return deal_msg
			except IOError as error:
				print("Problem with socket")
		else:
			print("Machine did not respond")			


	def router_routine(self):
		#port_number = "{}:9999".format(self.self_add)
		port_number = "152.228.1.124:9999"
		self.router = self.context.socket(zmq.ROUTER)
		self.router.bind("tcp://%s" % port_number)
		#print("Successfully binded to port %s for respondent" % self.port_number)

	def route(self):
		while True:
			ident = self.router.recv() # routing information
			delimiter = self.router.recv() # delimiter
			message = self.router.recv_json()
			reply_dict = {}

			for keys in message.keys():
				if key == "job_info":
					barcode = message.get("job_info", None)
					reply_dict = databaseServer.get_job(barcode)
				elif key == "sfu":
					pass
				elif key == "ink_key":
					ink_key = message.get("ink_key", None)
					databaseServer.replace_ink_key(ink_key)

			self.router.send(ident, zmq.SNDMORE)
			self.router.send(delimiter, zmq.SNDMORE)
			self.router.send_json(reply_dict)

	def request_jam(self):
		msg_dict = {}
		deal_msg = self.request(msg_dict)
		databaseServer.insert_jam(deal_msg)

	def send_job_info(self):
		msg_dict = databaseServer.get_all_job()
		self.request(msg_dict)

	def send_ink_key(self):
		msg_dict = database.get_ink_key()
		self.request(msg_dict)

	def send_emp(self):
		msg_dict = databaseServer.get_emp()
		self.request(msg_dict)

	def request_schedule(self):
		scheduler = apscheduler.schedulers.background.BackgroundScheduler()
		self.job = scheduler.add_job(self.request_jam, 'cron', minute='*/5', id='5mins')
		scheduler.start()

if __name__ == '__main__':
	NetworkManager()
