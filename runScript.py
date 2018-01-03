import os
import tkinter
import sensor.sensorReading as sensorReading


if __name__ == '__main__':
    os.system("sudo pigpiod")
    Root = tkinter.Tk()
    sensorReading.RaspberryPiController(Root)