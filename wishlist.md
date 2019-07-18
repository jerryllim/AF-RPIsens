### To Dos
* UPS using capacitor? Graceful shutdown
* x11vnc - Unable without desktop - use minimal desktop? https://www.raspberrypi.org/forums/viewtopic.php?t=133691
* Mender for OTA updates
* Easy updates for each individual RPi
* EDI with ebprod & auto import export
* (Optional) Select waste1 or waste2 as final option?
* (Optional) Use colour picker to pick bg colour?
* Change from 3 machines with 5 A pins to 4 machines with 4 A pins
* Multiprocessing for RPi
* Multiprocessing for Server

### Completed
1. Clone image for faster copying
2. Debug log to check if server received pi requests
3. Add to Server Machines Tab model to have empty first in Machine Details (Pi Tab)
4. Add decimal point for waste
5. Add a way to know which textinput is selected (AdjustmentScreen)
6. Add automatic way of determine whether to use FakeClass *sys.platform.startswith('linux')*
7. Added Quit button
8. Server to send jobs_table to pis
9. Remove machines.sqlite from Viewer
10. Add multiplier on the server to handle different UOMs (e.g. Pocket File)
11. Add multiplier on Pis (e.g. slitter with double output for single count)
12. Add 'sample' barcode
