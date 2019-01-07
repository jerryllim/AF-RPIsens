import sys
import zmq

port = "127.0.0.1:56789"

# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt_string(zmq.SUBSCRIBE, "Server")

print("Connecting to machine...")
socket.bind("tcp://%s" % port)
print("Successfully connected to machine %s" % port)

while True:

		#  Wait for message from publisher
		print("Waiting for progression updates...")
		message = str(socket.recv(), "utf-8")
		print("Received message: %s" % message)
