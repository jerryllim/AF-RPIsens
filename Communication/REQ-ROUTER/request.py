def requester_routine(self):
	  #port_number = "{}:9999".format(self.self_add)
	  port_number = "152.228.1.124:8888"
	  self.context = zmq.Context()
	  #print("Connecting to machine...")
	  self.requester = self.context.socket(zmq.REQ)
	  self.requester.connect("tcp://%s" % port_number)
    #print("Successfully connected to machine %s" % port_number)

def request(self):
    self.requester.send_string("request msg")
    print("request msg sent")
    recv_msg = self.requester.recv()
    print("recv_msg: %s" % recv_msg)
