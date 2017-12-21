import time
import zmq
import random
import json
import sys

def worker():
    #worker_id = random.randrange(1,10005)
    #print("I am worker #%s" % (worker_id))
    context = zmq.Context()
    # recieve work
    worker_receiver = context.socket(zmq.PULL)
    worker_receiver.connect("tcp://127.0.0.1:8677")
    # send work
    worker_sender = context.socket(zmq.PUSH)
    worker_sender.connect("tcp://127.0.0.1:8678")
    
    while True:
        message = str(worker_receiver.recv(), "utf-8")
        print("Request received: %s" % message)
        #data = work['num']
        #result = { 'worker' : worker_id, 'num' : data}
        #if data%2 == 0: 
        #    worker_sender.send_json(result)

        sensor_data = "123456789"

        msg = {
            'worker': 1,
            'data': sensor_data,
        }
        msg_json = json.dumps(msg)
        worker_sender.send_string(msg_json)
        time.sleep(1)

    worker_receiver.close()
    sys.close()

worker()