import sensor.sensorGUI as sensorGUI
import sensor.sensorGlobal as sensorGlobal
import RPi.GPIO as GPIO
import warnings


class RaspberryPiController:
    def __init__(self, root):
        GPIO.setmode(GPIO.BCM)
        self.dataHandler = sensorGlobal.DataHandler()
        self.mainWindow = sensorGUI.MainWindow(root, self)

        for pin, bounce in self.dataHandler.get_pin_and_bounce():
            RaspberryPiController.pin_setup(self, pin, bounce)

        self.mainWindow.start_gui()

    def pin_triggered(self, pin):
        _id = self.dataHandler.get_id_from_pin(pin)
        self.dataHandler.countDict.update([_id])
        self.mainWindow.count[_id].set(self.dataHandler.countDict[_id])

    def remove_detections(self):
        for pin, bounce in self.dataHandler.get_pin_and_bounce():
            GPIO.remove_event_detect(int(pin))

    def reset_pins(self):
        warnings.filterwarnings('ignore', '.*clean up.*', RuntimeWarning)
        try:
            self.pin_cleanup()
        finally:
            warnings.resetwarnings()
        GPIO.setmode(GPIO.BCM)
        for pin, bounce in self.dataHandler.get_pin_and_bounce():
            RaspberryPiController.pin_setup(self, pin, bounce)

    @staticmethod
    def pin_setup(caller, pin, bounce=50):
        GPIO.setup(int(pin), GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(int(pin), GPIO.RISING, callback=caller.pin_triggered, bouncetime=bounce)

    @staticmethod
    def pin_cleanup():
        GPIO.cleanup()
