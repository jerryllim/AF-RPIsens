import json
from collections import OrderedDict


class DataHandler:
    sensorDict = OrderedDict()
    countDict = {}
    pinToID = {}

    def __init__(self, file_name='sensorInfo.json'):
        self.fileName = file_name
        self.load_data()
        self.pinToID = self.list_pin_and_id()
        self.init_count()

    def save_data(self):
        with open(self.fileName, 'w') as outfile:
            json.dump(self.sensorDict, outfile)

    def load_data(self):
        try:
            with open(self.fileName, 'r') as infile:
                self.sensorDict = json.load(infile, object_pairs_hook=OrderedDict)
        except FileNotFoundError:
            pass

    def get_pins(self):
        temp = []
        for _id, (_name, _pin, _bounce) in self.sensorDict.items():
            temp.append(_pin)
        return temp

    def get_names(self):
        temp = []
        for _id, (_name, _pin, _bounce) in self.sensorDict.items():
            temp.append(_name)
        return temp

    def get_bounce(self):
        temp = []
        for _id, (_name, _pin, _bounce) in self.sensorDict.items():
            temp.append(_bounce)
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

    def get_id_from_pin(self, pin):
        return self.pinToID[pin]

    def init_count(self):
        for _id, _value in self.sensorDict.items():
            self.countDict[_id] = 0


class TempClass:
    def __init__(self, data_handler):
        self.dataHandler = data_handler


if __name__ == '__main__':
    dataHandler = DataHandler()

    if True:
        tempDict1 = {'S001': ("Sensor 1", 23, 50), 'S002': ("Sensor 2", 24, 50), 'S003': ("Sensor 3", 17, 50),
                     'S004': ("Sensor 4", 27, 50), 'S005': ("Sensor 5", 22, 50), 'S006': ("Sensor 6", 5, 50),
                     'S007': ("Sensor 7", 6, 50), 'S008': ("Sensor 8", 13, 50), 'S009': ("Sensor 9", 19, 50),
                     'S010': ("Sensor 10", 26, 50)}
        tempDict2 = OrderedDict()
        for key, value in tempDict1.items():
            tempDict2[key] = value

        dataHandler.sensorDict.clear()
        dataHandler.sensorDict.update(tempDict2)
        dataHandler.save_data()

        print(dataHandler.get_names())
        print(dataHandler.get_pins())

    if False:
        for pin in dataHandler.countDict.keys():
            print('{} is of type {}'.format(pin, type(pin)))
