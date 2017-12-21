import zmq
import random
import sys
import time

ports = ["9990","9991"]
context = zmq.Context()
socket = context.socket(zmq.PAIR)
for port in ports:
    print("Binding socket to port: " + str(port))
    socket.bind("tcp://*:%s" % port)
    print("Connection has been established")

while True:
    data = input("Enter: ")
    #data = "random data"
    if data == 'quit':
        socket.close()
        sys.exit()
    if len(str.encode(data)) > 0:
        socket.send_string(data)
        msg = str(socket.recv(), "utf-8")
        print("Received: %s" % msg)
        time.sleep(1)
