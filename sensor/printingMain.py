import zmq
import time
import json
import pigpio
import datetime
import threading
import printingkivy
from collections import Counter


class RaspberryPiController:
    bounce = 30
    pulse_pins = {}
    steady_pins = {}
    pin_to_name = {}
    counts = {}
    _output = 0
    publisher = None
    # states = {}

    def __init__(self, filename='pin_dict.json'):
        self.filename = filename
        self.load_pin_dict()
        self.pi = pigpio.pi()
        self.callbacks = []
        self.counts_lock = threading.Lock()
        self.publisher_routine()
        self.respondent_routine()
        self.gui = printingkivy.PrintingGUIApp(self)

        output_string = self.gui.config.get('General', 'output_pin')
        output_pin = int(output_string[-2:])
        for name, pin in self.pulse_pins.items():
            self.pin_setup(pin, (pin == output_pin))
        for name, pin in self.steady_pins.items():
            self.pin_setup2(pin)

        # self.gui.run()  # TODO uncomment

    def load_pin_dict(self):
        try:
            with open(self.filename, 'r') as infile:
                temp = json.load(infile)
                self.pulse_pins = temp["pulse"]
                self.steady_pins = temp["steady"]
                self.pin_to_name = self.lookup_pin_name()
        except FileNotFoundError:
            # TODO either log or stop program since not recording pins
            print("File not found, ", self.filename)
            raise SystemExit

    def lookup_pin_name(self):
        temp = {}
        for name, pin in self.pulse_pins.items():
            temp[pin] = name

        for name, pin in self.steady_pins.items():
            temp[pin] = name

        return temp

    def get_key(self, interval=5, emp=None):
        # TODO change to UTC now?
        now = datetime.datetime.now()
        # Floor to nearest interval (default = 5)
        now = now - datetime.timedelta(minutes=now.minute % interval)

        if not emp:
            emp = self.gui.action_bar.employees[1]

        if self.gui.current_job:
            jo_no = self.gui.current_job.get_current_job()
        else:
            jo_no = 'None'

        return '{0}_{1}_{2}'.format(emp, jo_no, now.strftime('%Y%m%d%H%M'))

    def pin_triggered(self, pin, _level, _tick):
        name = self.pin_to_name[pin]
        key = self.get_key()
        self.update_count(name, key)

    def output_pin_triggered(self, pin, _level, _tick):
        self.pin_triggered(pin, _level, _tick)

        # TODO store output here? and to FeRAM?
        self._output += 1
        self.gui.update_output()

    def pin_setup(self, pin, is_output, bounce=30):
        self.pi.set_mode(pin, pigpio.INPUT)
        self.pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
        self.pi.set_glitch_filter(pin, (bounce * 1000))
        if is_output:
            self.callbacks.append(self.pi.callback(pin, pigpio.RISING_EDGE, self.output_pin_triggered))
        else:
            self.callbacks.append(self.pi.callback(pin, pigpio.RISING_EDGE, self.pin_triggered))

    def pin_setup2(self, pin, bounce=30):
        self.pi.set_mode(pin, pigpio.INPUT)
        self.pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
        self.pi.set_glitch_filter(pin, (bounce * 1000))
        self.callbacks.append(self.pi.callback(pin, pigpio.EITHER_EDGE, self.pin_triggered2))
        # self.states[pin] = 0

    def update_count(self, name, key):
        with self.counts_lock:
            if self.counts.get(name) is None:
                self.counts[name] = Counter()
            self.counts[name].update([key])

    def get_counts(self):
        with self.counts_lock:
            temp = self.counts.copy()
            self.counts.clear()

        return json.dumps(temp)
    
        def respondent_routine(self):
        port_number = "152.228.1.124:9999"

        self.context = zmq.Context()
        self.respondent = self.context.socket(zmq.REP)
        self.respondent.setsockopt(zmq.LINGER, 0)
        self.resondent.bind("tcp://%s" % self.port_number)
        #print("Successfully binded to port %s for respondent" % self.port_number)

    def respond(self, msg):
        # routine functions begins here
        while True:
            # wait for next request from client
            _message = str(self.respondent.recv(), "utf-8")
            #print("Received request (%s)" % _message)
            time.sleep(1)
            res_json = msg
            self.respondent.send_string(res_json)

    def run_thread(self):
        # spins a new thread for respond while loop
        respondent_thread = threading.Thread(target=self.respond)
        respondent_thread.start()
    
    def publisher_routine(self):
        # port connection sould be declared beforehand
        port = "152.228.1.124:56789"

        # establishing context, publisher pattern and connection to server port
        context = zmq.Context()
        self.publisher = context.socket(zmq.PUB)
        self.publisher.connect("tcp://%s" % port)
        time.sleep(1)
        # print("Successfully connected to machine %s" % port)

    def publish(self, msg):
        # routine function starts here
        msg_json = msg
        if self.publisher is not None:
            self.publisher.send_string(msg_json)
        else:
            self.publisher_routine()

    def pin_triggered2(self, pin, level, _tick):
        name = self.pin_to_name[pin]
        # self.states[name] = level

        key = self.get_key(interval=1)

        if level and not self.counts[name][key]:
            self.update_count(name, key)

    # TODO for apscheduler to call once a minute
    def check_pin_states(self):
        for pin in self.steady_pins:
            state = self.pi.read(pin)
            if state:
                name = self.pin_to_name[pin]
                key = self.get_key(interval=1)
                self.update_count(name, key)
