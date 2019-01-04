import sensor.v1.sensorGUI as sensorGUI
import sensor.v1.sensorGlobal as sensorGlobal
import pigpio
import datetime
from collections import Counter
import logging


class RaspberryPiController:
    def __init__(self, root):
        # Logger setup
        self.logger = logging.getLogger('afRPIsens')
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler('afRPIsens.log')
        file_handler.setLevel(logging.DEBUG)
        log_format = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s: %(module)s - %(message)s')
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)
        self.logger.info('Started program')

        self.pinDataManager = sensorGlobal.PinDataManager()
        self.networkDataManager = sensorGlobal.NetworkDataManager(self.pinDataManager)
        self.networkDataManager.rep_start()
        self.dataManager = sensorGlobal.DataManager(self.pinDataManager, self.networkDataManager)
        self.mainWindow = sensorGUI.MainGUI(root, self)
        self.pi = pigpio.pi()
        self.callbacks = []
        self.logger.info('Completed initial setup')

        for pin, bounce in self.pinDataManager.get_pin_and_bounce_list():
            RaspberryPiController.pin_setup(self, pin, bounce)
        self.logger.info('Completed pin setup')

        self.logger.info('Starting GUI')
        self.mainWindow.start_gui()

    def pin_triggered(self, pin, _level, _tick):
        _id = self.pinDataManager.get_id_from_pin(pin)
        now = datetime.datetime.utcnow()
        now = now - datetime.timedelta(minutes=now.minute % 5)
        datetime_stamp = now.strftime('%Y-%m-%d %H:%M')
        self.pinDataManager.increase_countDict(_id, datetime_stamp)
        self.mainWindow.count[_id].set(sum(self.pinDataManager.countDict[_id].values()) +
                                       sum(self.networkDataManager.removedCount.get(_id, Counter()).values()))
        
    def remove_detections(self):
        for callback in self.callbacks:
            callback.cancel()

    def reset_pins(self):
        self.logger.debug('Resetting pins')
        self.remove_detections()
        for pin, bounce in self.pinDataManager.get_pin_and_bounce_list():
            RaspberryPiController.pin_setup(self, pin, bounce)

    def pin_setup(self, pin, bounce=30):
        self.pi.set_mode(pin, pigpio.INPUT)
        self.pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
        self.pi.set_glitch_filter(pin, (bounce * 1000))
        self.callbacks.append(self.pi.callback(pin, pigpio.RISING_EDGE, self.pin_triggered))


class TempClass:  # Used for internal testing TODO remove once not needed
    def __init__(self, root):
        # Logger setup
        self.logger = logging.getLogger('afRPIsens')
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler('afRPIsens.log')
        file_handler.setLevel(logging.DEBUG)
        log_format = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s: %(module)s - %(message)s')
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)

        self.pinDataManager = sensorGlobal.PinDataManager()
        self.networkDataManager = sensorGlobal.NetworkDataManager(self.pinDataManager)
        # self.networkDataManager.rep_start()
        self.dataManager = sensorGlobal.DataManager(self.pinDataManager, self.networkDataManager)
        self.mainWindow = sensorGUI.MainGUI(root, self)
        self.logger.info('Completed initial setup')

        self.logger.info('Starting GUI')
        self.mainWindow.start_gui()

    def reset_pins(self):
        self.logger.debug('Resetting pins')
        pass

    def pin_triggered(self, pin, _level, _tick):
        _id = self.pinDataManager.get_id_from_pin(pin)
        datetime_stamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.pinDataManager.increase_countDict(_id, datetime_stamp)
        self.mainWindow.count[_id].set(sum(self.pinDataManager.countDict[_id].values()) +
                                       sum(self.networkDataManager.removedCount[_id].get(_id, Counter()).values()))
