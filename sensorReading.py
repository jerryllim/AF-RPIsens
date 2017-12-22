import sensorGUI
import sensorGlobal
import RPi.GPIO as GPIO


class RaspberryPiController:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.dataHandler = sensorGlobal.DataHandler()
        self.mainWindow = sensorGUI.MainWindow(self.dataHandler)

        for pin in self.dataHandler.get_pins():
            GPIO.setup(int(pin), GPIO.IN)
            GPIO.add_event_detect(int(pin), GPIO.RISING, callback=self.pin_triggered)

        self.mainWindow.start_gui()

    def pin_triggered(self, port):
        self.dataHandler.countDict[port] = (self.dataHandler.countDict[port] + 1)
        self.mainWindow.count[str(port)].set(self.dataHandler.countDict[port])


if __name__ == '__main__':
    RaspberryPiController()
