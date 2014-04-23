#!/usr/bin/python

import sys; sys.path.insert(0, "libs")
from zaber.device.interface import *
from zaber.device.port.emulator import *
from zaber.device.emulator.ascii import *

debug = True
device1 = EmulatorASCIIDeviceSingleAxis(debug=debug)
device2 = EmulatorASCIIDeviceSingleAxis(debug=debug)

z = InterfaceASCII(
      port_class=ZaberPortEmulatorASCII,
      devices=[device1,device2],
      debug=debug,
    )

z.home()

for i in range(20):
    time.sleep(0.1)

exit()

eng = EmulatorASCIIEngine(devices=[device1,device2],debug=debug)
eng.start()
eng.writeline('/renumber')
eng.writeline('/')
eng.writeline('/get comm.address')
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

for i in range(20):
    s = eng.read()
    if s: 
        print "OUTPUT:", s,
    else:
        time.sleep(0.1)

eng.join()



