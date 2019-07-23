### To Dos
* UPS using capacitor? Graceful shutdown
* x11vnc - Unable without desktop - use minimal desktop? https://www.raspberrypi.org/forums/viewtopic.php?t=133691
* Mender for OTA updates
* Easy updates for each individual RPi (Set jam.sqlite, jam_machines.txt & pigui.ini in different folder?)
* EDI with ebprod & auto import export
* Edit auto import to handle multiple naming for ebprod
* Change from 3 machines with 5 A pins to 4 machines with 4 A pins
* Multiprocessing for RPi
* Multiprocessing for Server
* Change BackgroundScheduler in serverGUI (for DisplayTable updates) to QtScheduler (using QClock internally? or create new Scheduler class?)
* Change jam_past_table to csv/excel/sqlite file
* Add new tables for qc, maintenance, emp_shift
* Server to send jobs_table to pis based on like mac [where umachine LIKE "%ZP%"]
* Add current jo_no, date_time table
* Add barcode scanner support
* (Optional) Use colour picker to pick bg colour? Or just more colour options

### Completed
1. Clone image for faster copying
2. Debug log to check if server received pi requests
3. Add to Server Machines Tab model to have empty first in Machine Details (Pi Tab)
4. Add decimal point for waste
5. Add a way to know which textinput is selected (AdjustmentScreen)
6. Add automatic way of determine whether to use FakeClass *sys.platform.startswith('linux')*
7. Added Quit button
8. Server to send jobs_table to pis based on mac [where umachine_no in (1,2,3)]
9. Remove machines.sqlite from Viewer
10. Add multiplier on the server to handle different UOMs (e.g. Pocket File)
11. Add multiplier on Pis (e.g. slitter with double output for single count)
12. Add 'sample' barcode


### Waste App
1. Separate waste input device
2. Android or RPi
