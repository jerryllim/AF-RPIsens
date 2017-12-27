import sensor.sensorGUI as sensorGUI
import sensor.sensorGlobal as sensorGlobal
import RPi.GPIO as GPIO
import tkinter  # TODO remove when not needed


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
        self.dataHandler.countDict[_id] = (self.dataHandler.countDict[_id] + 1)
        self.mainWindow.count[_id].set(self.dataHandler.countDict[_id])

    def reset_pins(self):
        RaspberryPiController.pin_cleanup()
        for pin, bounce in self.dataHandler.get_pin_and_bounce():
            RaspberryPiController.pin_setup(self, pin, bounce)

    @staticmethod
    def pin_setup(caller, pin, bounce=50):
        GPIO.setup(int(pin), GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(int(pin), GPIO.RISING, callback=caller.pin_triggered, bouncetime=bounce)

    @staticmethod
    def pin_cleanup():
        GPIO.cleanup()


if __name__ == '__main__':
    Root = tkinter.Tk()  # TODO try script
    RaspberryPiController(Root)
