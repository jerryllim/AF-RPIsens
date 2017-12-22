import zmq
import time
import sys
import json

port = "9201"
if len(sys.argv) > 1:
    port =  sys.argv[1]
    int(port)

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:%s" % port)

while True:
    #  Wait for next request from client
    message = str(socket.recv(), "utf-8")
    print("Received request: ", message)
    time.sleep (1)
    msgDict = {
        'sensor': "7",
        'data': "987654321",
        'client': "9201",
    }
    msg_json = json.dumps(msgDict)
    socket.send_string(msg_json)
    #socket.send_string("Client from port %s" % port)