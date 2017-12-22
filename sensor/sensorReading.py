import GUI.sensorGUI as sensorGUI
import sensorGlobal as sensorGlobal
import RPi.GPIO as GPIO


class RaspberryPiController:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.dataHandler = sensorGlobal.DataHandler()
        self.mainWindow = sensorGUI.MainWindow(self.dataHandler)

        for pin in self.dataHandler.get_pins():
            RaspberryPiController.pin_setup(pin)

        self.mainWindow.start_gui()

    def pin_triggered(self, pin):
        self.dataHandler.countDict[pin] = (self.dataHandler.countDict[pin] + 1)
        self.mainWindow.count[str(pin)].set(self.dataHandler.countDict[pin])

    @staticmethod
    def pin_setup(self, pin):
        GPIO.setup(int(pin), GPIO.IN)
        GPIO.add_event_detect(int(pin), GPIO.RISINg, callback=self.pin_triggered, bouncetime=30)


if __name__ == '__main__':
    RaspberryPiController()
