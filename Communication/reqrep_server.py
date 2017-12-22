import zmq
import sys
import time
import json

#if len(sys.argv) > 1:
#    port =  sys.argv[1]
#    int(port)

#if len(sys.argv) > 2:
#    port1 =  sys.argv[2]
#    int(port1)

ports = ["9200","9201"]

context = zmq.Context()
print("Connecting to port...")
socket = context.socket(zmq.REQ)
for port in ports:
    socket.connect("tcp://localhost:%s" % port)
    print("Successfully connected to port %s" % port)
#socket.connect("tcp://localhost:%s" % port2)
#if len(sys.argv) > 2:
#    socket.connect ("tcp://localhost:%s" % port1)

#while True:
    #data = input("Enter: ")
    #data = "random data"
    #if data == 'quit':
    #    socket.close()
    #    sys.exit()
    #if len(str.encode(data)) > 0:
    #   socket.send_string(data)
    #    msg = str(socket.recv(), "utf-8")
    #    print("Received: ",msg)
for request in range(1, 3):
    print("Sending request ", request,"...")
    socket.send_string("Sensor Data")
    #  Get the reply.
    msg_json = socket.recv()
    ds = json.loads(msg_json)
    #msg = str(socket.recv(), "utf-8")
    print("Sensor: %s :: Data: %s :: Client: %s" % (ds['sensor'], ds['data'], ds['client']))
    #print("Received reply ", request, "[", msg, "]")
    time.sleep(1)