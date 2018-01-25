import zmq
import json

ports = ["127.0.0.1:9304", "127.0.0.1:9301"]

context = zmq.Context()
print("Connecting to machine...")
socket = context.socket(zmq.DEALER)
socket.setsockopt(zmq.LINGER, 0)
for port in ports:
    socket.connect("tcp://%s" % port)
    print("Successfully connected to machine %s" % port)

for request in range(len(ports)):
    print("Sending request ", request, "...")
    socket.send_string("", zmq.SNDMORE)  # delimiter
    socket.send_string("Sensor Data")  # actual message

    # use poll for timeouts:
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    socks = dict(poller.poll(5 * 1000))

    if socket in socks:
        try:
            socket.recv()  # discard delimiter
            msg_json = socket.recv()  # actual message
            sens = json.loads(msg_json)
            response = "Sensor: %s :: Data: %s :: Client: %s" % (sens['sensor'], sens['data'], sens['client'])
            print("Received reply ", request, "[", response, "]")
        except IOError:
            print("Could not connect to machine")
    else:
        print("Machine did not respond")
