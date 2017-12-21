import zmq
import random
import sys
import time

port = "9990"
context = zmq.Context()
socket = context.socket(zmq.PAIR)
print("Binding socket to port: " + str(port))
socket.connect("tcp://localhost:%s" % port)
print("Connected")

count = 0
response = 1

while True:
    msg = str(socket.recv(), "utf-8")
    print("Received: %s" % msg)
    count = count + 1
    print("Counter: ",count)

    if count == response:
        data = "Client has received message from server: " + msg
        socket.send_string(data)
        response = response + 1
        time.sleep(1)

# Close connection
socket.close()
sys.exit()
