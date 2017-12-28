import pigpio


def cbf(gpio, level, tick):
    global count
    print('GPIO: ', gpio, ' has ', count)

count = 0
pi = pigpio.pi()
some = pi.callback(23, func=)
print(some)
