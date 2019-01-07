import zmq
import time
import json
import random

port = "9998" # multiple similar clients but just with different ports
subscriber = "27.0.0.1:56789"

context = zmq.Context()

# reply
respondent = context.socket(zmq.REP)
respondent.bind("tcp://*:%s" % port)
print("Successfully binded to port %s for respondent" % port)


# publish
publisher = context.socket(zmq.PUB)
publisher.connect("tcp://%s" % subscriber)
print("Successfully connected to server %s for subscriber" % subscriber)

# Initialize poll set
poller = zmq.Poller()
poller.register(respondent, zmq.POLLIN)
poller.register(publisher, zmq.POLLOUT)
print("Successfully registered poll set")

# Process messages from both sockets
while True:
    try:
        sockets = dict(poller.poll())
    except KeyboardInterrupt:
        break

    if respondent in sockets:
        #  Wait for next request form server
        message = str(respondent.recv(), "utf-8")
        # process task
        print("Received request: ", message)
        time.sleep(1)
        msgDict = {
            'sensor': "6",
            'data': "123456789",
            'client': "9876",
        }
        msg_json = json.dumps(msgDict)
        respondent.send_string(msg_json)

    if publisher in sockets:
        data = input("Type a message to publish\n") # user input
        topic = "Server"
        messagedata = random.randrange(1,215) - 80 # random messagedata
        print("%s %d %s" % (topic, messagedata, data))
        publisher.send_string("%s %d %s" % (topic, messagedata, data))
        time.sleep(1)
