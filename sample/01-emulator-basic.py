#!/usr/bin/python

import time
import pprint

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

pprint.pprint(device._settings)
