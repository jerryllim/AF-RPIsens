import logging
import json
import zmq
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import server.v1.serverDB as serverDB


class CommunicationManager:
    REQUEST_ID = 'request'

    def __init__(self, server_settings: serverDB.ServerSettings, database: serverDB.DatabaseManager, server_run):
        self.logger = logging.getLogger('afRPIsens_server')
        self.server_settings = server_settings
        self.database = database
        self.server_run = server_run
        self.scheduler = BackgroundScheduler()
        self.address_ports = []
        self.context = None
        self.socket = None
        self.set_jobs()
        self.scheduler.start()

    def req_client(self):
        self.address_ports = list(self.server_settings.machine_ports.items())

        self.context = zmq.Context()
        self.logger.debug("Connecting to the ports")
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)
        for (name, (address, port)) in self.address_ports:
            self.socket.connect("tcp://{}:{}".format(address, port))
            self.logger.debug("Successfully connected to machine at {}:{}".format(address, port))

        for index in range(len(self.address_ports)):
            # print("Sending request ", index, "...")
            self.socket.send_string("", zmq.SNDMORE)  # delimiter
            self.socket.send_string("Sensor Data")  # actual message

            # use poll for timeouts:
            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLIN)

            socks = dict(poller.poll(5 * 1000))
            (name, (address, port)) = self.address_ports[index]
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
                            table_name = "'{}:{}'".format(name, uniq_id)
                            self.database.insert_to_database(table_name, timestamp, count)
                except IOError:
                    self.logger.warning('Could not connect to machine {}, {}'.format(machine, port))
            else:
                self.logger.warning('Machine did not respond, ({}:{})'.format(machine, port))

            self.server_run.update_live_table()

    def set_jobs(self):
        self.scheduler.remove_all_jobs()
        interval = self.server_settings.misc_settings[self.server_settings.REQUEST_TIME]
        cron_trigger = CronTrigger(hour='*', minute='*/{}'.format(interval))
        self.scheduler.add_job(self.req_client, cron_trigger, id=CommunicationManager.REQUEST_ID)
