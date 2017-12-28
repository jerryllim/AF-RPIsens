import datetime
import threading
from collections import Counter
import time


class MyCounter:
    def __init__(self):
        self.lock = threading.Lock()
        self._counter = Counter()

    def get_counter(self, value):
        return self._counter[value]

    def set_counter(self, value):
        with self.lock:
            print('Added by ', threading.current_thread().getName())
            self._counter.update([value])


def increase_counter(some, thing, times=2):
    print(threading.current_thread().getName(), ' will execute ', times * 5, ' times.')
    for index in range(times * 5):
        some.set_counter(thing)
        print('Count is ', some.get_counter(thing), ' by ', threading.current_thread().getName(), ' at ',
              datetime.datetime.now().strftime('%X'))
        time.sleep(2)


if False:
    c = MyCounter()
    names = ['First', 'Second']
    threading.current_thread().setName('MAIN')
    for i in range(2):
        t = threading.Thread(target=increase_counter, args=(c, 'some', i+1))
        t.setName(names[i])
        t.start()

    for thread in threading.enumerate():
        print('Trying to end ', thread.getName())
        if thread.getName() != 'MAIN':
            thread.join()
            print('Ended ', thread.getName())
        else:
            print('Whoops it is MAIN')
    print('Ended all thread!!!')

if False:
    c = Counter()
    c.update(['some'])
    print('c is ', hex(id(c)))
    print('c is ', c)
    d = c
    print('d is ', hex(id(d)))
    print('c is ', d)
    c = Counter()
    c.update(['some', 'some'])
    print('c is ', hex(id(c)))
    print('c is ', c)
    print('d is ', hex(id(d)))
    print('c is ', d)

