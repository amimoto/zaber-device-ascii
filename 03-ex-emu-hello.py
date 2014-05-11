#!/usr/bin/python

import sys; sys.path.insert(0, "libs")

import pprint

from zaber.device.ascii.interface import *
from zaber.device.ascii.emulator.ascii import *
from zaber.device.ascii.port.emulator import *

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

z = InterfaceHelpers(port=port)

print z.autodetect(renumber=True)

