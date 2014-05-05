#!/usr/bin/python

import sys; sys.path.insert(0, "libs")

import pprint
import datetime

from zaber.device.interface import *
from zaber.device.port.emulator import *
from zaber.device.emulator.ascii import *

debug = True
debug = False

axes_settings = [
  {
    'pos': 10000,
    'limit.approach.maxspeed': 3000
  }
]

settings = {
  'deviceid': 65535,
  'comm.address': 2,
  'axes_settings': axes_settings
}

device = EmulatorASCIIDeviceSingleAxis(
                settings=settings,
                debug=debug
            )

port = ZaberPortEmulatorASCII(
            devices=[device],
            debug=debug
          )

z = InterfaceASCIIHelpers(port=port)

print "--------------------------------------------------"
print "Autodetecting"
print "--------------------------------------------------"

devices = z.autodetect(renumber=True)

print "Autodetected:", devices

z = InterfaceASCIIHelpers(port=port,devices=devices)

print "--------------------------------------------------"
print "Sending device 1 axis 1 to home"
print "--------------------------------------------------"

z[1][1].home()
start_home_time = datetime.datetime.now()

for i in range(100):
    time.sleep(0.1)
    r = z.request()
    if r and r[1].warn_flags == 'IDLE':
        end_home_time = datetime.datetime.now()
        homing_delta = end_home_time - start_home_time
        print "Homed in {} seconds".format(homing_delta.seconds)
        print "Received data was:", r
        break
