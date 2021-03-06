    def router_routine(self):
        port = "152.228.1.124:8888"
        self.context = zmq.Context()
        self.router = self.context.socket(zmq.ROUTER)
        self.router.bind("tcp://%s" % port)

        # Initialize a poll set
        #poller = zmq.Poller()
        #poller.register(frontend, zmq.POLLIN)

    def route(self):
        while True:
            # first 2 recv() strips away the routing info and delimiter
            self.router.recv() # routing information
            self.router.recv() # delimiter
            _message = str(self.router.recv())
            print("Received request: %s" % _message)
            ok_msg = "ok msg"
            self.router.send_string(ok_msg)
