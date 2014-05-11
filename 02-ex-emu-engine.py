#!/usr/bin/python

import sys; sys.path.insert(0, "libs")

import pprint

from zaber.device.ascii.port.emulator import *
from zaber.device.ascii.emulator import *

debug = True

axes_settings = [
  {
    'pos': 10000
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

port = ZaberPortEmulator(
            devices=[device],
            debug=debug
          )

port.writeline('/renumber 2')
port.writeline('/get pos')

def read_a_bit(iterations):
    for i in range(iterations):
        s = port.read()
        if s: 
            print "OUTPUT:", s,
        else:
            time.sleep(0.1)

port.writeline('/get pos')
read_a_bit(5)
port.writeline('/set pos 100')

print device.position_stats()

read_a_bit(5)


