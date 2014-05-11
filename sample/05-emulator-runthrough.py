#!/usr/bin/python

import time

from zaber.device.ascii.emulator import *
from zaber.device.ascii.port.emulator import *
from zaber.device.ascii import *

debug = True

axes_settings = [
  {
    'pos': 1000000
  }
]

settings = {
  'deviceid': 65535,
  'comm.address': 2,
  'axes_settings': axes_settings
}

device = EmulatorDeviceSingleAxis(
                settings=settings,
                debug=debug
            )

port = PortEmulator(
            devices=[device],
            debug=debug
          )

z = Interface(port=port)

time.sleep(0.2)

print "--------------------------------------------------"
print "z.request('renumber'):", z.request('renumber')
time.sleep(0.1)
print "--------------------------------------------------"
print "z[1][1].target:", z[1][1].target
time.sleep(0.1)
print "--------------------------------------------------"
print "z.s.pos[1]:", z.s.pos[1]
time.sleep(0.1)
print "--------------------------------------------------"
print "z[1][1].home():", z[1][1].home()
time.sleep(0.1)
print "--------------------------------------------------"
print "z.s.pos[1]:", z.s.pos[1]
time.sleep(0.1)
print "--------------------------------------------------"
print "z.s:", z.s
time.sleep(0.1)
print "--------------------------------------------------"
print "z[1][0].s:", z[1][0].s
time.sleep(0.1)
print "--------------------------------------------------"
print "z[1][0].s.deviceid:", z[1][0].s.deviceid
time.sleep(0.1)
print "--------------------------------------------------"
print "z[1][0].s.deviceid():", z[1][0].s.deviceid()
time.sleep(0.1)
print "--------------------------------------------------"
print "z.s.deviceid:", z.s.deviceid
time.sleep(0.1)
print "--------------------------------------------------"
try:
    print "z.s.deviceid[0]:", z.s.deviceid[0]
except:
    print "Exception happened as expected"
time.sleep(0.1)
print "--------------------------------------------------"
print "z.s.pos[1]:", z.s.pos[1]
time.sleep(0.1)
print "--------------------------------------------------"
print "z.s.pos[1][1]:", z.s.pos[1][1]
time.sleep(0.1)
print "--------------------------------------------------"
try:
    print "z.s.pos[1][1]:", z[1].renumber(2)
except:
    print "Exception happened as expected"
time.sleep(0.1)
print "--------------------------------------------------"
print "z.s.pos[2]:", z.s.pos[2]
time.sleep(0.1)
print "--------------------------------------------------"
print "z.s.pos[2][1] = 100"
z.s.pos[2][1] = 100
time.sleep(0.1)
print "--------------------------------------------------"
print "z[2][1].s.pos = 200"
z[2][1].s.pos = 200
time.sleep(0.1)
print "--------------------------------------------------"
print "z[2].s.pos[1] = 300"
z[2].s.pos[1] = 300
time.sleep(0.1)
print "--------------------------------------------------"




