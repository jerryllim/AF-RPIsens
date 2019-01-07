import zmq
import time
import json
import threading
import random

def publisher_routine():
    context = zmq.Context()
    subscriber = "27.0.0.1:56789"

    # publish
    publisher = context.socket(zmq.PUB)
    publisher.connect("tcp://%s" % subscriber)
    print("Successfully connected to server %s for subscriber" % subscriber)

    while True:
        data = input("Type a message to publish\n") # user input
        topic = "Server"
        messagedata = random.randrange(1,215) - 80 # random messagedata
        print("%s %d %s" % (topic, messagedata, data))
        publisher.send_string("%s %d %s" % (topic, messagedata, data))
        time.sleep(1)

def respondent_routine():
    port = "9998" # multiple similar clients but just with different ports

    context = zmq.Context()

    # reply
    respondent = context.socket(zmq.REP)
    respondent.bind("tcp://*:%s" % port)
    print("Successfully binded to port %s for respondent" % port)

    while True:
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

def main():
    respondent_thread = threading.Thread(target=respondent_routine)
    publisher_thread = threading.Thread(target=publisher_routine)
    respondent_thread.start()
    publisher_thread.start()

if __name__ == "__main__":
    main()
