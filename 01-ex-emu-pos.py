#!/usr/bin/python

import sys; sys.path.insert(0, "libs")
import pprint
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

pprint.pprint(device._settings)



