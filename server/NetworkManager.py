import zmq
import json
import time


class NetworkManager():
	def __init__(self):
		self.context = zmq.Context()
		self.requester_routine()
		self.respondent_routine()

	def requester_routine(self):
		#port_number = "{}:8888".format(self.self_add)
		port_number = "152.228.1.124:8888"
		self.requester = self.context.socket(zmq.REQ)
		self.requester.connect("tcp://%s" % port_number)
		#print("Successfully connected to machine %s" % port_number)

	def request(self):
		self.requester.send_string("request msg")
		print("request msg sent")
		recv_msg = str(self.requester.recv())
		print("recv_msg: %s" % recv_msg)

	def respondent_routine(self):
		#port_number = "{}:9999".format(self.self_add)
		port_number = "152.228.1.124:9999"
		self.respondent = self.context.socket(zmq.REP)
		self.respondent.setsockopt(zmq.LINGER, 0)
		self.respondent.bind("tcp://%s" % port_number)
		#print("Successfully binded to port %s for respondent" % self.port_number)

	def respond(self):
		while True:
			# wait for next request from client
			_message = str(self.respondent.recv())
			# print("Received request (%s)" % _message)
			res_json = self.get_counts()
			self.respondent.send_string(res_json)


if __name__ == '__main__':
	NetworkManager()
