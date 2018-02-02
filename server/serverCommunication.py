import logging
import json
import zmq
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import server.serverDB as serverDB


class Communication:
    REQUEST_ID = 'request'

    def __init__(self, server_settings: serverDB.ServerSettings, database: serverDB.DatabaseManager):
        self.logger = logging.getLogger('afRPIsens_server')
        self.server_settings = server_settings
        self.database = database
        self.scheduler = BackgroundScheduler()
        self.ports = []
        self.context = None
        self.socket = None

    def req_client(self):

        self.ports = list(self.server_settings.machine_ports.values())

        self.context = zmq.Context()
        self.logger.debug("Connecting to the ports")
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)
        for port in self.ports:
            self.socket.connect("tcp://{}".format(port))
            self.logger.debug("Successfully connected to machine at {}".format(port))

        for index in range(len(self.ports)):
            print("Sending request ", index, "...")
            self.socket.send_string("", zmq.SNDMORE)  # delimiter
            self.socket.send_string("Sensor Data")  # actual message

            # use poll for timeouts:
            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLIN)

            socks = dict(poller.poll(5 * 1000))
            port = self.ports[index]
            # get machine name for port
            for machine, _port in self.server_settings.machine_ports.items():
                if _port == port:
                    break

            if self.socket in socks:
                try:
                    self.socket.recv()  # discard delimiter
                    msg_json = self.socket.recv()  # actual message
                    sens = json.loads(msg_json)
                    for uniq_id, values in sens.items():
                        for timestamp, count in values.items():
                            table_name = ""'{}:{}'"".format(port, uniq_id)
                            self.database.insert_to_database(table_name, timestamp, count)
                except IOError:
                    self.logger.warning('Could not connect to machine {}, {}'.format(machine, port))
            else:
                self.logger.warning('Machine did not respond, ({}:{})'.format(machine, port))

    def set_jobs(self):
        self.scheduler.remove_all_jobs()
        cron_trigger = CronTrigger(hour='*', minute='*/15')  # TODO set here
        self.scheduler.add_job(self.req_client, cron_trigger, id=Communication.REQUEST_ID)
