# Tasks
## RPi
- [x] add new unique identifier 
- [x] add individual debounce time
- [x] check debounce problem
- [ ] add communication component
- [x] check open socket -> **always open**
- [ ] RPi NTPd: https://raspberrypi.stackexchange.com/questions/24079/how-to-use-ntp-on-raspberry-pi-by-local-ntp-server
- [x] add schedule to transfer data -> **Hardcode time interval?**
- [x] How often to reset screen values? Same as scheduled data transfer?
- [x] added namedtuple for easier reading *share named tuple between server and client?* 
- [x] change count dict to collection.Counter
- [ ] add log
- [x] change RPi.GPIO to pigpio
- [ ] Remodel GUI to more OO
- [x] auto resize font -> **Fullscreen + one font change**
- [ ] set to clear IntVar once an hour (new list?)
- [x] launch pigpiod at startup -> **added to runScript**
- [ ] change to executable file?

## Server
- [x] add log.txt for log purposes
- [x] add timer options
- [x] add terminal listbox to contain reply data
- [ ] determine computer specifications
- [x] add timestamps in view
- [x] change listbox to treeview
- [ ] change client side message format to match machine
- [ ] parsing json -> csv -> excel log
