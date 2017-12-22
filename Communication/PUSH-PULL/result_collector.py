import time
import zmq
import pprint
import json

def result_collector():
    context = zmq.Context()
    results_receiver = context.socket(zmq.PULL)
    results_receiver.bind("tcp://127.0.0.1:8678")
    #collecter_data = {}
    #for x in range(1000):
    #    result = results_receiver.recv_json()
    #    if (result['worker']) in collecter_data:
    #        collecter_data[result['worker']] = collecter_data[result['worker']] + 1
    #    else:
    #        collecter_data[result['worker']] = 1
    #    if x == 999:
    #        pprint.pprint(collecter_data)

    msg = results_receiver.recv()
    ds = json.loads(msg)

    print("%s :: %s" % (ds['worker'], ds['data']))
 
result_collector()