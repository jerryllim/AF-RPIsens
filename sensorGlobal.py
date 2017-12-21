import json
from collections import OrderedDict


class DataHandler:
    sensorArray = OrderedDict()

    def __init__(self, file_name='testFile.txt'):  # TODO change default file name
        self.fileName = file_name
        self.load_data()

    def save_data(self):
        with open(self.fileName, 'w') as outfile:
            json.dump(self.sensorArray, outfile)

    def load_data(self):
        with open(self.fileName, 'r') as infile:
            self.sensorArray = json.load(infile, object_pairs_hook=OrderedDict)

    def get_names(self):
        return list(self.sensorArray.keys())

    def get_pins(self):
        pin_list = []
        for key in self.sensorArray.keys():
            pin_list.append(self.sensorArray[key])
        return pin_list
    

if __name__ == '__main__':
    dataHandler = DataHandler()

    print(dataHandler.get_names())
    print(dataHandler.get_pins())

    tempDict = {"Sensor 1": 23, "Sensor 2": 24, "Sensor 3": 17, "Sensor 4": 27, "Sensor 5": 22, "Sensor 6": 5,
                "Sensor 7": 6, "Sensor 8": 12, "Sensor 9": 19, "Sensor 10": 26}
    # dataHandler.sensorArray.clear()
    dataHandler.sensorArray.update(tempDict)
    dataHandler.save_data()

    print(dataHandler.get_names())
    print(dataHandler.get_pins())
