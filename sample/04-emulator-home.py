#!/usr/bin/python

from __future__ import print_function

import sys; sys.path.insert(0, "..")

import pprint
import datetime

from zaber.device.ascii.interface import *
from zaber.device.ascii.emulator import *
from zaber.device.ascii.port.emulator import *

debug = True
#debug = False

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

device = EmulatorDeviceSingleAxis(
                settings=settings,
                debug=debug
            )

port = PortEmulator(
            devices=[device],
            debug=debug
          )

z = Interface(port=port,debug=debug)

print("--------------------------------------------------")
print("Autodetecting")
print("--------------------------------------------------")

devices = z.autodetect(renumber=True)

print("Autodetected:", devices)

print("--------------------------------------------------")
print("Sending device 1 axis 1 to home")
print("--------------------------------------------------")

z[1][1].home()
start_home_time = datetime.datetime.now()

for i in range(100):
    time.sleep(0.1)
    r = z[1].query()
    if r.status == 'IDLE':
        end_home_time = datetime.datetime.now()
        homing_delta = end_home_time - start_home_time
        print("Homed in {} seconds".format(homing_delta.seconds))
        print("Received data was:", r)
        break

