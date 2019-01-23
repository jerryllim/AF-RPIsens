    self.context = zmq.Context()
    self.router_routine()
    self.publisher_routine()
    
    def router_routine(self):
        port = "152.228.1.124:8888"
        self.router = self.context.socket(zmq.ROUTER)
        self.router.bind("tcp://%s" % port)

        # Initialize a poll set
        #poller = zmq.Poller()
        #poller.register(frontend, zmq.POLLIN)

    def route(self):
        while True:
            # first 2 recv() strips away routing info and delimiter
            self.router.recv() #routing information
            self.router.recv() #delimiter
            _message = str(self.router.recv())
            print("received")
            print("Received request: %s" % _message)
            ok_msg = "ok msg"
            self.router.send_string(ok_msg)

    def publisher_routine(self):
        port = "152.228.1.135:56788"

        # publisher pattern and connection to server port
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.connect("tcp://%s" % port)
        time.sleep(1)  # Wait for publisher to connect to port
        # print("Successfully connected to machine %s" % port)

    def publish(self):
        # routine function begins here
        msg_json = "publisher's msg"

        self.publisher.send_string(msg_json)
