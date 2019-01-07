import json
import pigpio
import datetime
import threading
from collections import Counter, namedtuple

sensorInfo = namedtuple('sensorInfo', ['pin', 'bounce'])


class RaspberryPiController:
    sensor_dict = {}
    pin_to_name = {}
    counts = {}

    def __init__(self, filename='pin_dict.json'):
        self.filename = filename
        self.load_pin_dict()
        self.pi = pigpio.pi()
        self.callbacks = []
        self.counts_lock = threading.Lock()

        for name, (pin, bounce) in self.sensor_dict.items():
            self.pin_setup(pin, bounce)

        # TODO start GUI

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

    def pin_triggered(self, pin, _level, _tick):
        name = self.pin_to_name[pin]
        now = datetime.datetime.utcnow()
        now = now - datetime.timedelta(minutes=now.minute % 5)
        datetime_stamp = now.strftime('%Y-%m-%d %H:%M')
        self.update_count(name, datetime_stamp)
        # TODO Add update the string in GUI

    def pin_setup(self, pin, bounce=30):
        self.pi.set_mode(pin, pigpio.INPUT)
        self.pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
        self.pi.set_glitch_filter(pin, (bounce * 1000))
        self.callbacks.append(self.pi.callback(pin, pigpio.RISING_EDGE, self.pin_triggered))

    def update_count(self, name, datetime_stamp):
        with self.counts_lock:
            if self.counts.get(name) is None:
                self.counts[name] = Counter()
            self.counts[name].update(datetime_stamp)
