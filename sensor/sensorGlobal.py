import json
from collections import OrderedDict


class DataHandler:
    sensorDict = OrderedDict()
    countDict = {}

    def __init__(self, file_name='sensorInfo.json'):  # TODO change default file name
        self.fileName = file_name
        self.load_data()
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
        return list(self.sensorDict.keys())

    def get_names(self):
        return list(self.sensorDict.values())

    def init_count(self):
        for _pin, _name in self.sensorDict.items():
            self.countDict[int(_pin)] = 0


class TempClass:
    def __init__(self, data_handler):
        self.dataHandler = data_handler


if __name__ == '__main__':
    dataHandler = DataHandler()

    if True:
        tempDict1 = {"Sensor 1": 23, "Sensor 2": 24, "Sensor 3": 17, "Sensor 4": 27, "Sensor 5": 22, "Sensor 6": 5,
                     "Sensor 7": 6, "Sensor 8": 12, "Sensor 9": 19, "Sensor 10": 26}
        tempDict2 = OrderedDict()
        for name, pin in tempDict1.items():
            tempDict2[pin] = name

        dataHandler.sensorDict.clear()
        dataHandler.sensorDict.update(tempDict2)
        dataHandler.save_data()

        print(dataHandler.get_names())
        print(dataHandler.get_pins())

    if False:
        for pin in dataHandler.countDict.keys():
            print('{} is of type {}'.format(pin, type(pin)))
