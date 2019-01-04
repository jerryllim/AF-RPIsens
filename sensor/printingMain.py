import pigpio
import datetime
import json
from collections import Counter, namedtuple

sensorInfo = namedtuple('sensorInfo', ['pin', 'bounce'])


class RaspberryPiController:
    sensor_dict = {}
    pin_to_name = {}

    def __init__(self, filename='pin_dict.json'):
        self.filename = filename
        self.load_pin_dict()
        # TODO add threading.lock?

    def load_pin_dict(self):
        try:
            with open(self.filename, 'r') as infile:
                pin_dict = json.load(infile)
                for name in pin_dict.keys():
                    self.sensor_dict[name] = sensorInfo(**(pin_dict[name]))
                self.pin_to_name = self.lookup_pin_name()

        except FileNotFoundError:
            pass

    def lookup_pin_name(self):
        temp = {}
        for name, (pin, bounce) in self.sensor_dict.items():
            temp[pin] = name

        return temp
