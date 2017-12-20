import sensorGUI
import sensorGlobal
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

for pin in sensorGlobal.pinArraypins:
    GPIO.setup(pin, GPIO.IN)


def pin_triggered(port):
    pin_no = sensorGlobal.pinArray.index(port)
    sensorGUI.count[pin_no].set(sensorGUI.sums[pin_no].get() + 1)


if __name__ == '__main__':
    try:
        for pin in sensorGlobal.pinArray:
            GPIO.add_event_detect(pin, GPIO.RISING, callback=pin_triggered)

        dataHandler = sensorGlobal.DataHandler()
        sensorGUI.start_gui()

    except KeyboardInterrupt:
        print("Quit")
        GPIO.cleanup()
