import tkinter
import sensor.sensorReading as sensorReading


if __name__ == '__main__':
    Root = tkinter.Tk()
    sensorReading.RaspberryPiController(Root)
