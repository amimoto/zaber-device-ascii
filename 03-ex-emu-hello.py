#!/usr/bin/python

import sys; sys.path.insert(0, "libs")

import pprint

from zaber.device.interface import *
from zaber.device.port.emulator import *
from zaber.device.emulator.ascii import *

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

device = EmulatorASCIIDeviceSingleAxis(
                settings=settings,
                debug=debug
            )

port = ZaberPortEmulatorASCII(
            devices=[device],
            debug=debug
          )

z = InterfaceASCIIHelpers(port=port)

print z.autodetect(renumber=True)

