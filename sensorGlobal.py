import json

pinArray = (23, 24, 17, 27, 22, 5, 6, 13, 19, 26)
sensorNameArray = ('Sensor 1', 'Sensor 2', 'Sensor 3', 'Sensor 4', 'Sensor 5', 'Sensor 6', 'Sensor 7', 'Sensor 8',
                   'Sensor 9', 'Sensor 10')
sensorsArray = {'Sensor 1': 23, 'Sensor 2': 24, 'Sensor 3': 17, 'Sensor 4': 27, 'Sensor 5': 22, 'Sensor 6': 5,
               'Sensor 7': 6, 'Sensor 8': 13, 'Sensor 9': 19, 'Sensor 10': 26}


class DataHandler:
    sensorArray = {}

    def __init__(self, file_name='testFile.txt'):  # TODO change default file name
        self.fileName = file_name
        self.load_data()

    def save_data(self):
        with open(self.fileName, 'w') as outfile:
            json.dump(self.sensorArray, outfile)

    def load_data(self):
        with open(self.fileName, 'r') as infile:
            self.sensorArray = json.load(infile)

