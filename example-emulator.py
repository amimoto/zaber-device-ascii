#!/usr/bin/python

import sys; sys.path.insert(0, "libs")
from zaber.device.interface import *
from zaber.device.port.emulator import *
from zaber.device.emulator.ascii import *

debug = True
debug = False
device1 = EmulatorASCIIDeviceSingleAxis(debug=debug)
device2 = EmulatorASCIIDeviceSingleAxis(debug=debug)

if 1:
    port = ZaberPortEmulatorASCII(devices=[device1,device2],debug=debug)
    z = InterfaceASCIIHelpers(port=port)

    print "Autodetecting..."
    print z.autodetect(renumber=True)
    print "Done autodetecting..."
    #print z.renumber()
    #print z.renumber(nonblock=True)

    for i in range(20):
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



