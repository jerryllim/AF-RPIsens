import sensor.sensorGUI as sensorGUI
import sensor.sensorGlobal as sensorGlobal
import pigpio
import datetime
from collections import Counter


class RaspberryPiController:
    def __init__(self, root):
        self.pinDataManager = sensorGlobal.PinDataManager()
        self.networkDataManager = sensorGlobal.NetworkDataManager(self.pinDataManager)
        self.networkDataManager.rep_start()
        self.dataManager = sensorGlobal.DataManager(self.pinDataManager, self.networkDataManager)
        self.mainWindow = sensorGUI.MainGUI(root, self)
        self.pi = pigpio.pi()
        self.callbacks = []

        for pin, bounce in self.pinDataManager.get_pin_and_bounce_list():
            RaspberryPiController.pin_setup(self, pin, bounce)

        self.mainWindow.start_gui()

    def pin_triggered(self, pin, level, tick):
        _id = self.pinDataManager.get_id_from_pin(pin)
        datetime_stamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.pinDataManager.increase_countDict(_id, datetime_stamp)
        self.mainWindow.count[_id].set(sum(self.pinDataManager.countDict[_id].values()) +
                                       sum(self.networkDataManager.removedCount.get(_id, Counter()).values()))
        
    def remove_detections(self):
        for callback in self.callbacks:
            callback.cancel()

    def reset_pins(self):
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
        self.pinDataManager = sensorGlobal.PinDataManager()
        self.networkDataManager = sensorGlobal.NetworkDataManager(self.pinDataManager)
        # self.networkDataManager.rep_start()
        self.dataManager = sensorGlobal.DataManager(self.pinDataManager, self.networkDataManager)
        self.mainWindow = sensorGUI.MainGUI(root, self)

        self.mainWindow.start_gui()

    def reset_pins(self):
        pass

    def pin_triggered(self, pin, level, tick):
        _id = self.pinDataManager.get_id_from_pin(pin)
        datetime_stamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.pinDataManager.increase_countDict(_id, datetime_stamp)
        self.mainWindow.count[_id].set(sum(self.pinDataManager.countDict[_id].values()) +
                                       sum(self.networkDataManager.removedCount[_id].get(_id, Counter()).values()))
