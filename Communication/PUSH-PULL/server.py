import time
import zmq

def server():
    context = zmq.Context()
    zmq_socket = context.socket(zmq.PUSH)
    zmq_socket.bind("tcp://127.0.0.1:8677")
    
    # Start your result manager and workers before you start your servers

    #for num in range(20000):
    #    work_message = { 'num' : num }
    #    zmq_socket.send_json(work_message)
    zmq_socket.send_string("Please export data")
    print("Request sent!")

server()
