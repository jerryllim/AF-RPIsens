import json
import zmq
import logging
import sqlite3


class Communication:
    def __init__(self, filename='portSettings.json'):
        self.logger = logging.getLogger('afRPIsens_server')
        self.filename = filename
        self.ports = []
        self.context = None
        self.socket = None

    def req_client(self):

        with open(self.filename, 'r') as infile:
            machines_port = json.load(infile)

        machines, self.ports = map(list, zip(*machines_port))

        self.context = zmq.Context()
        self.logger.debug("Connecting to the ports")
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)
        for port in self.ports:
            self.socket.connect("tcp://%s" % port)
            self.logger.debug("Successfully connected to machine %s" % port)

        for request in range(len(self.ports)):
            print("Sending request ", request, "...")
            self.socket.send_string("", zmq.SNDMORE)  # delimiter
            self.socket.send_string("Sensor Data")  # actual message

            # use poll for timeouts:
            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLIN)

            socks = dict(poller.poll(5 * 1000))

            if self.socket in socks:
                try:
                    self.socket.recv()  # discard delimiter
                    msg_json = self.socket.recv()  # actual message
                    sens = json.loads(msg_json)
                    # TODO edit here
                    for timestamp, values in sens.items():
                        for uniqID, count in values.items():
                            response = "Time: %s :: Data: %s :: Client: %s :: Sensor: %s" % (uniqID, count, port, timestamp)
                            print("Received reply ", request, "[", response, "]")
                except IOError:
                    print("Could not connect to machine")
            else:
                # TODO machine not respond
                print("Machine did not respond")


class DatabaseManager:
    def __init__(self, database_name='afRPIsens.sqlite'):
        self.database_name = database_name
        pass

    def create_table(self, table_name, database=None):
        if database is None:
            database = self.database_name
        db = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
        try:
            db.execute("DROP TABLE IF EXISTS {}".format(table_name))
            db.execute("CREATE TABLE IF NOT EXISTS {} (time TIMESTAMP PRIMARY KEY NOT NULL, quantity INTEGER NOT NULL)"
                       .format(table_name))
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    def insert_into_table(self, table_name, timestamp, quantity, database=None):
        if database is None:  # Check for database name
            database = self.database_name
        # Establish connection and create table if not exists
        db = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
        db.execute("CREATE TABLE IF NOT EXISTS {} (time TIMESTAMP PRIMARY KEY NOT NULL, quantity INTEGER NOT NULL)"
                   .format(table_name))
        # Check if exist same timestamp for machine
        cursor = db.cursor()
        cursor.execute("SELECT * from {} WHERE time=datetime(?)", (timestamp,))
        query = cursor.fetchone()
        if query:  # TODO to test
            _timestamp, count = query
            quantity = quantity + count
            cursor.execute("UPDATE {} SET quantity = ? WHERE time = ?", (quantity, timestamp))
        else:
            cursor.execute("INSERT INTO {} VALUES(datetime(?), ?".format(table_name), (timestamp, quantity))
