# Tasks
## RPi
- [x] add new unique identifier 
- [x] add individual debounce time
- [x] check debounce problem
- [x] add communication component
- [x] check open socket -> **always open**
- [x] RPi NTPd: https://raspberrypi.stackexchange.com/questions/24079/how-to-use-ntp-on-raspberry-pi-by-local-ntp-server
- [x] add schedule to transfer data -> **Hardcode time interval?**
- [x] How often to reset screen values? Same as scheduled data transfer?
- [x] added namedtuple for easier reading *share named tuple between server and client?* 
- [x] change count dict to collection.Counter
- [x] add log
- [x] change RPi.GPIO to pigpio
- [x] auto resize font -> **Fullscreen + one font change**
- [x] set to clear IntVar once an hour (new list?) -> **Added new Counter**
- [x] launch pigpiod at startup -> **added to runScript**
- [ ] Remodel GUI to more OO
- [ ] disable screen sleep
- [ ] force to sync time at boot
- [ ] auto launch app after boot
- [ ] create desktop launcher
- [x] create executable file

## Server
- [x] add log.txt for log purposes
- [x] add timer options
- [x] add terminal listbox to contain reply data
- [x] determine computer specifications
- [x] add timestamps in view
- [x] change listbox to treeview
- [x] change client side message format to match machine
- [x] handling multiple clients
- [x] introducing timeout with polling for server request
- [x] embed updatable graphs - https://pythonprogramming.net/plotting-live-bitcoin-price-data-tkinter-matplotlib/
- [x] Add Misc Settings
- [x] Directory chooser - http://effbot.org/zone/tkinter-directory-chooser.htm
- [x] Today/Current for quick access
- [x] Connect communication component
- [x] create executable file
- [ ] database management, convert past data to reduce storage
- [ ] move file location -> shutil.move - https://docs.python.org/3/library/shutil.ht

## Both
- [ ] Add UTC time for both RPi and Server? Database
- [ ] Create setup guide
