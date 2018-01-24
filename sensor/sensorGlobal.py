import json
import zmq
import time
from collections import OrderedDict
from collections import Counter
from collections import namedtuple
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import logging


sensorInfo = namedtuple('sensorInfo', ['name', 'pin', 'bounce'])


class NetworkDataManager:
    REMOVED_ID = 'removedID'
    PORT_NUMBER = 'portNumber'

    def __init__(self, pin_data_manager):
        self.logger = logging.getLogger('afRPIsens')
        self.pinDataManager = pin_data_manager
        self.scheduler = BackgroundScheduler()
        self.removed_minutes = '60'
        self.removedCount = {}
        self.removedLock = threading.Lock()
        self.port_number = '9999'
        self.logger.debug('Completed setup')

    def get_content(self):
        temp = self.pinDataManager.clear_countDict()
        self.transfer_to_removed(temp)
        return temp

    def transfer_to_removed(self, temp):
        self.logger.debug('Transferring to removed')
        with self.removedLock:
            for _key in temp.keys():
                if self.removedCount.get(_key, None) is None:
                    self.removedCount[_key] = temp[_key]
                else:
                    self.removedCount[_key].update(temp[_key])
        self.logger.debug('Completed transfer')

    def rep_data(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.connect("tcp://*:{}".format(self.port_number))

        while True:
            #  Wait for next request from client
            _message = str(socket.recv(), "utf-8")
            self.logger.info('Received request ({})'.format(_message))
            time.sleep(1)
            msg_json = json.dumps(self.get_content())
            socket.send_string(msg_json)
            self.logger.info('Sent data')

    def rep_start(self):
        thread = threading.Thread(target=self.rep_data)
        thread.start()

    def clear_removed_count(self):
        with self.removedLock:
            self.removedCount.clear()
        self.logger.debug('Cleared removed count')

    def to_save_settings(self):
        return {NetworkDataManager.REMOVED_ID: self.removed_minutes, NetworkDataManager.PORT_NUMBER: self.port_number}

    def to_load_settings(self, temp_dict):
        self.removed_minutes = temp_dict.get(NetworkDataManager.REMOVED_ID, self.removed_minutes)
        self.port_number = temp_dict.get(NetworkDataManager.PORT_NUMBER, self.port_number)

    def add_jobs(self):
        if not self.scheduler.get_jobs():  # To prevent duplicating jobs
            hour, minute = NetworkDataManager.get_cron_hour_minute(self.removed_minutes)
            self.scheduler.add_job(self.clear_removed_count, 'cron', hour=hour, minute=minute, second=1,
                                   id=NetworkDataManager.REMOVED_ID)

    def set_removed_time(self, temp):
        if temp is None:
            temp = self.removed_minutes
        else:
            self.removed_minutes = temp
        hour, minute = NetworkDataManager.get_cron_hour_minute(temp)
        self.scheduler.reschedule_job(NetworkDataManager.REMOVED_ID, trigger='cron', hour=hour, minute=minute, second=1)

    def set_port_number(self, number):
        self.port_number = number

    def start_schedule(self):
        self.scheduler.start()

    @staticmethod
    def get_cron_hour_minute(temp):
        minutes = int(temp)
        if minutes//60 == 0:
            hour = '*'
        else:
            hour = '*/' + str(minutes//60)

        if minutes % 60 == 0:
            minute = '*'
        else:
            minute = '*/' + str(minutes % 60)
        return hour, minute


class PinDataManager:
    sensorDict = OrderedDict()
    countDict = {}
    pinToID = {}

    def __init__(self, file_name='sensorInfo.json'):
        self.logger = logging.getLogger('afRPIsens')
        self.fileName = file_name
        self.pinToID = None
        self.countDictLock = threading.Lock()
        self.logger.debug('Completed setup')

    def to_save_settings(self):
        temp_dict = OrderedDict()
        for unique_id, named_tuple in self.sensorDict.items():
            temp_dict[unique_id] = named_tuple._asdict()
        return temp_dict

    def to_load_settings(self, temp_dict):
        for unique_id in temp_dict.keys():
            temp_info = sensorInfo(**(temp_dict[unique_id]))
            self.sensorDict[unique_id] = temp_info
            with self.countDictLock:
                self.countDict[unique_id] = Counter()
        self.pinToID = self.list_pin_and_id()

    def get_pins_list(self):
        temp = []
        for _id in self.sensorDict.keys():
            temp.append(self.sensorDict[_id].pin)
        return temp

    def get_names_list(self):
        temp = []
        for _id in self.sensorDict.keys():
            temp.append(self.sensorDict[_id].name)
        return temp

    def get_bounce_list(self):
        temp = []
        for _id in self.sensorDict.keys():
            temp.append(self.sensorDict[_id].bounce)
        return temp

    def get_pin_and_bounce_list(self):
        temp = []
        for _id, (_name, _pin, _bounce) in self.sensorDict.items():
            temp.append((_pin, _bounce))
        return temp

    def get_id_list(self):
        return list(self.sensorDict.keys())

    def list_pin_and_id(self):
        temp = {}
        for _id, (_name, _pin, _bounce) in self.sensorDict.items():
            temp[_pin] = _id
        return temp

    def get_id_from_pin(self, _pin):
        return self.pinToID[_pin]

    def reset_sensorDict(self, dictionary):
        self.sensorDict.clear()
        self.sensorDict.update(dictionary)
        self.pinToID = self.list_pin_and_id()

    def get_sensorDict_items(self):
        return self.sensorDict.items()

    def get_sensorDict_item(self, _id):
        return self.sensorDict[_id]

    def set_countDict_item(self, _id, count):
        with self.countDictLock:
            if self.countDict.get(_id, None) is None:
                self.countDict[_id] = Counter()
            self.countDict[_id] = count

    def increase_countDict(self, _id, datetime_stamp):
        with self.countDictLock:
            if self.countDict.get(_id) is None:
                self.countDict[_id] = Counter()
            self.countDict[_id].update([datetime_stamp])

    def get_countDict_item(self, _id):
        with self.countDictLock:
            return self.countDict[_id]

    def del_countDict_item(self, _id):
        with self.countDictLock:
            del self.countDict[_id]

    def clear_countDict(self):
        with self.countDictLock:
            temp_count = self.countDict.copy()
            self.countDict.clear()
            return temp_count


class DataManager:
    PIN_CONFIG_KEY = 'PinConfig'
    NETWORK_CONFIG_KEY = 'NetworkConfig'

    def __init__(self, pin_data_manager, network_data_manager, filename='settings.json'):
        self.logger = logging.getLogger('afRPIsens')
        self.pinDataManager = pin_data_manager
        self.networkDataManager = network_data_manager
        self.fileName = filename
        self.load_data()
        self.logger.debug('Completed setup')

    def save_data(self):
        self.logger.debug('Saving data')
        temp_dict = self.pinDataManager.to_save_settings()
        temp_dict2 = self.networkDataManager.to_save_settings()
        settings_dict = {DataManager.PIN_CONFIG_KEY: temp_dict, DataManager.NETWORK_CONFIG_KEY: temp_dict2}
        with open(self.fileName, 'w') as outfile:
            json.dump(settings_dict, outfile)
        self.logger.debug('Saved data')

    def load_data(self):
        self.logger.debug('Loading data')
        try:
            with open(self.fileName, 'r') as infile:
                settings_dict = json.load(infile, object_pairs_hook=OrderedDict)
                self.pinDataManager.to_load_settings(settings_dict[DataManager.PIN_CONFIG_KEY])
                self.networkDataManager.to_load_settings(settings_dict[DataManager.NETWORK_CONFIG_KEY])
        except FileNotFoundError:
            pass
        finally:
            self.networkDataManager.add_jobs()
            self.networkDataManager.start_schedule()
        self.logger.debug('Loaded data')


if __name__ == '__main__':
    pinManager = PinDataManager()
    networkManager = NetworkDataManager(pinManager)
    dataManager = DataManager(pinManager, networkManager)
    dataManager.save_data()

    if False:
        tempDict1 = {'S001': sensorInfo("Sensor 1", 23, 50), 'S002': sensorInfo("Sensor 2", 24, 50),
                     'S003': sensorInfo("Sensor 3", 17, 50), 'S004': sensorInfo("Sensor 4", 27, 50),
                     'S005': sensorInfo("Sensor 5", 22, 50), 'S006': sensorInfo("Sensor 6", 5, 50),
                     'S007': sensorInfo("Sensor 7", 6, 50), 'S008': sensorInfo("Sensor 8", 13, 50),
                     'S009': sensorInfo("Sensor 9", 19, 50), 'S010': sensorInfo("Sensor 10", 26, 50)}
        tempDict2 = OrderedDict()
        for key, value in tempDict1.items():
            tempDict2[key] = value

        pinManager.sensorDict.clear()
        pinManager.sensorDict.update(tempDict2)

        print(pinManager.get_names_list())
        print(pinManager.get_pins_list())

    if False:
        dataManager.save_data()
