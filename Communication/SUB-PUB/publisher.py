import zmq
import random
import sys
import time

port = "127.0.0.1:56789"

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.connect("tcp://%s" % port)
print("Successfully connected to machine %s" % port)

while True:

	data = input("Type a message to publish\n")
	topic = "Server"
	messagedata = random.randrange(1,215) - 80 # random messagedata
	print("%s %d %s" % (topic, messagedata, data))
	socket.send_string("%s %d %s" % (topic, messagedata, data))
	time.sleep(1)
