import sensorGUI
import sensorGlobal
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

pins = (23, 24, 17, 27, 22, 5, 6, 13, 19, 26)

for pin in sensorGlobal.pinArraypins:
    GPIO.setup(pin, GPIO.IN)


def pin_triggered(pin):
    pin_no = sensorGlobal.pinArray.index(pin)
    sensorGUI.sums[pin_no].set(sensorGUI.sums[pin_no].get() + 1)


if __name__ == '__main__':
    try:
        for pin in sensorGlobal.pinArray:
            GPIO.add_event_detect(pin, GPIO.RISING, callback=pin_triggered)

        sensorGUI.start_gui()

    except KeyboardInterrupt:
        print("Quit")
        GPIO.cleanup()
