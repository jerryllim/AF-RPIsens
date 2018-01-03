import json
from collections import OrderedDict
from collections import Counter
from collections import namedtuple
import threading
import datetime
from apscheduler.schedulers.background import BackgroundScheduler


sensorInfo = namedtuple('sensorInfo', ['name', 'pin', 'bounce'])


class NetworkDataManager:
    TRANSFER_ID = 'transferID'
    SAVE_ID = 'saveID'
    REMOVED_ID = 'removedID'

    def __init__(self, data_handler):
        self.storeDict = {}
        self.dataHandler = data_handler
        self.scheduler = BackgroundScheduler()
        self.transfer_minutes = '1'
        self.save_minutes = '5'
        self.removedCount = Counter()
        self.removedLock = threading.Lock()

    def transfer_info(self):
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        temp_counter = self.dataHandler.clear_countDict()
        with self.removedLock:
            self.removedCount.update(temp_counter)
        self.storeDict[time] = temp_counter

    def save_data(self):
        with open('jsonData.json', 'a') as outfile:
            json.dump(self.storeDict, outfile)
        self.storeDict.clear()

    def clear_removed_count(self):
        with self.removedLock:
            self.removedCount.clear()

    def to_save_settings(self):
        return {NetworkDataManager.SAVE_ID: self.save_minutes, NetworkDataManager.TRANSFER_ID: self.transfer_minutes}

    def to_load_settings(self, temp_dict):
        self.transfer_minutes = temp_dict[NetworkDataManager.TRANSFER_ID]
        self.save_minutes = temp_dict[NetworkDataManager.SAVE_ID]

    def add_jobs(self):
        if not self.scheduler.get_jobs():  # To prevent duplicating jobs
            self.scheduler.add_job(self.transfer_info, 'cron', minute='*/' + self.transfer_minutes,
                                   id=NetworkDataManager.TRANSFER_ID)
            self.scheduler.add_job(self.save_data, 'cron', minute='*/' + self.save_minutes, second='30',
                                   id=NetworkDataManager.SAVE_ID)
            self.scheduler.add_job(self.clear_removed_count, 'cron', hour='*/1', minute='59',
                                   id=NetworkDataManager.REMOVED_ID)

    def set_transfer_time(self, temp=None):
        if temp is None:
            temp = self.transfer_minutes
        else:
            self.transfer_minutes = temp
        hour, minute = NetworkDataManager.get_cron_hour_minute(temp)
        self.scheduler.reschedule_job(NetworkDataManager.TRANSFER_ID, trigger='cron', hour=hour, minute=minute)

    def set_save_time(self, temp):
        if temp is None:
            temp = self.save_minutes
        else:
            self.save_minutes = temp
        hour, minute = NetworkDataManager.get_cron_hour_minute(temp)
        self.scheduler.reschedule_job(NetworkDataManager.SAVE_ID, trigger='cron', hour=hour, minute=minute, second=30)

    def set_removed_time(self, temp):
        if temp is None:
            temp = self.save_minutes
        else:
            self.save_minutes = temp
        hour, minute = NetworkDataManager.get_cron_hour_minute(temp)
        self.scheduler.reschedule_job(NetworkDataManager.REMOVED_ID, trigger='cron', hour=hour, minute=minute, second=1)

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
    countDict = Counter()
    pinToID = {}

    def __init__(self, file_name='sensorInfo.json'):
        self.fileName = file_name
        self.pinToID = None
        self.countDictLock = threading.Lock()

    def to_save_settings(self):
        temp_dict = OrderedDict()
        for unique_id, named_tuple in self.sensorDict.items():
            temp_dict[unique_id] = named_tuple._asdict()
        return temp_dict

    def to_load_settings(self, temp_dict):
        for unique_id in temp_dict.keys():
            temp_info = sensorInfo(**(temp_dict[unique_id]))
            self.sensorDict[unique_id] = temp_info
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
            self.countDict[_id] = count

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
        self.pinDataManager = pin_data_manager
        self.networkDataManager = network_data_manager
        self.fileName = filename
        self.load_data()

    def save_data(self):
        temp_dict = self.pinDataManager.to_save_settings()
        temp_dict2 = self.networkDataManager.to_save_settings()
        settings_dict = {DataManager.PIN_CONFIG_KEY: temp_dict, DataManager.NETWORK_CONFIG_KEY: temp_dict2}
        with open(self.fileName, 'w') as outfile:
            json.dump(settings_dict, outfile)

    def load_data(self):
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


class TempClass:  # Used for internal testing TODO remove once not needed
    def __init__(self):
        self.pinDataManager = PinDataManager()
        self.networkDataManager = NetworkDataManager(self.pinDataManager)
        self.dataManager = DataManager(self.pinDataManager, self.networkDataManager)

    def reset_pins(self):
        pass


if __name__ == '__main__':
    pinManager = PinDataManager()
    networkManager = NetworkDataManager(pinManager)
    dataManager = DataManager(pinManager, networkManager)
    dataManager.save_data()

    if False:
        tempDict1 = {'S001': sensorInfo("Sensor 1", 23, 50), 'S002': sensorInfo("Sensor 2", 24, 50), 'S003': sensorInfo("Sensor 3", 17, 50),
                     'S004': sensorInfo("Sensor 4", 27, 50), 'S005': sensorInfo("Sensor 5", 22, 50), 'S006': sensorInfo("Sensor 6", 5, 50),
                     'S007': sensorInfo("Sensor 7", 6, 50), 'S008': sensorInfo("Sensor 8", 13, 50), 'S009': sensorInfo("Sensor 9", 19, 50),
                     'S010': sensorInfo("Sensor 10", 26, 50)}
        tempDict2 = OrderedDict()
        for key, value in tempDict1.items():
            tempDict2[key] = value

        pinManager.sensorDict.clear()
        pinManager.sensorDict.update(tempDict2)
        pinManager.save_settings()

        print(pinManager.get_names_list())
        print(pinManager.get_pins_list())

    if True:
        dataManager.save_data()
