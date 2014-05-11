#!/usr/bin/python

import sys; sys.path.insert(0, "libs")

import pprint

from zaber.device.interface import *
from zaber.device.port.emulator import *
from zaber.device.emulator.ascii import *

debug = True
#debug = False
device1 = EmulatorASCIIDeviceSingleAxis(pos=10000,debug=debug)
device2 = EmulatorASCIIDeviceSingleAxis(debug=debug)

port = ZaberPortEmulatorASCII(devices=[device1,device2],debug=debug)
devices = {1: {'address': 1, 'axiscount': 0, 'deviceid': 65535},
           2: {'address': 2, 'axiscount': 0, 'deviceid': 65535}}

z = InterfaceASCIIHelpers(port=port,devices=devices)

print "Autodetecting..."
pprint.pprint(z.autodetect(renumber=True))
print "Done autodetecting..."

# Send a broadcast message
print "--------------------------------------------------"
z.home()
for i in range(20):
    s = port.read()
    if s: 
        print "OUTPUT:", s,
    else:
        time.sleep(0.1)


# print z.autodetect()
exit()

eng = EmulatorASCIIEngine(devices=[device1,device2],debug=debug)
eng.start()
eng.writeline('/renumber')

eng.writeline('/1 0 get deviceid')
for i in range(10):
    s = eng.read()
    if s: 
        print "OUTPUT:", s,
    else:
        time.sleep(0.1)


if 0:
    eng.writeline('/')
    eng.writeline('/get deviceid.address')
    eng.writeline('/set maxspeed 153600')
    eng.writeline('/help')
    eng.writeline('/move vel 20000')
    for i in range(10):
        eng.writeline('/')
        s = eng.read()
        if s: 
            print "OUTPUT:", s,
        else:
            time.sleep(0.1)
    eng.writeline('/1 estop')
    time.sleep(1)
    eng.writeline('/estop')

print "-----------------------------------------"
eng.writeline('/1 0 get deviceid')
for i in range(30):
    s = eng.read()
    if s: 
        print "OUTPUT:", s,
    else:
        time.sleep(0.1)

eng.join()



