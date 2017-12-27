import json
from collections import OrderedDict
from collections import Counter
from collections import namedtuple


sensorInfo = namedtuple('sensorInfo', ['name', 'pin', 'bounce'])


class DataHandler:
    sensorDict = OrderedDict()
    countDict = Counter()
    pinToID = {}

    def __init__(self, file_name='sensorInfo.json'):
        self.fileName = file_name
        self.load_data()
        self.pinToID = self.list_pin_and_id()
        # self.init_count()  # TODO remove if Counter works

    def save_data(self):
        with open(self.fileName, 'w') as outfile:
            temp_dict = OrderedDict()
            for unique_id, named_tuple in self.sensorDict.items():
                temp_dict[unique_id] = named_tuple._asdict()
            json.dump(temp_dict, outfile)
        self.pinToID = self.list_pin_and_id()

    def load_data(self):
        try:
            with open(self.fileName, 'r') as infile:
                temp_dict = json.load(infile, object_pairs_hook=OrderedDict)
            for unique_id in temp_dict.keys():
                temp_info = sensorInfo(**(temp_dict[unique_id]))
                self.sensorDict[unique_id] = temp_info
        except FileNotFoundError:
            pass

    def get_pins(self):
        temp = []
        for _id in self.sensorDict.keys():
            temp.append(self.sensorDict[_id].pin)
        return temp

    def get_names(self):
        temp = []
        for _id in self.sensorDict.keys():
            temp.append(self.sensorDict[_id].name)
        return temp

    def get_bounce(self):
        temp = []
        for _id in self.sensorDict.keys():
            temp.append(self.sensorDict[_id].bounce)
        return temp

    def get_pin_and_bounce(self):
        temp = []
        for _id, (_name, _pin, _bounce) in self.sensorDict.items():
            temp.append((_pin, _bounce))
        return temp

    def get_id(self):
        return list(self.sensorDict.keys())

    def list_pin_and_id(self):
        temp = {}
        for _id, (_name, _pin, _bounce) in self.sensorDict.items():
            temp[_pin] = _id
        return temp

    def get_id_from_pin(self, _pin):
        return self.pinToID[_pin]

    def init_count(self):  # TODO remove when Counter works
        for _id, _value in self.sensorDict.items():
            self.countDict[_id] = 0


class TempClass:
    def __init__(self, data_handler):
        self.dataHandler = data_handler


if __name__ == '__main__':
    dataHandler = DataHandler()

    if True:
        tempDict1 = {'S001': sensorInfo("Sensor 1", 23, 50), 'S002': sensorInfo("Sensor 2", 24, 50), 'S003': sensorInfo("Sensor 3", 17, 50),
                     'S004': sensorInfo("Sensor 4", 27, 50), 'S005': sensorInfo("Sensor 5", 22, 50), 'S006': sensorInfo("Sensor 6", 5, 50),
                     'S007': sensorInfo("Sensor 7", 6, 50), 'S008': sensorInfo("Sensor 8", 13, 50), 'S009': sensorInfo("Sensor 9", 19, 50),
                     'S010': sensorInfo("Sensor 10", 26, 50)}
        tempDict2 = OrderedDict()
        for key, value in tempDict1.items():
            tempDict2[key] = value

        dataHandler.sensorDict.clear()
        dataHandler.sensorDict.update(tempDict2)
        dataHandler.save_data()

        print(dataHandler.get_names())
        print(dataHandler.get_pins())

    if False:
        for a_pin in dataHandler.countDict.keys():
            print('{} is of type {}'.format(a_pin, type(a_pin)))
