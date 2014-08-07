#!/usr/bin/python

"""

Using the metadata ability to attach useful information to particular devices and peripherals

"""

from __future__ import print_function

import sys; sys.path.insert(0, "..")

import time

from zaber.device.ascii.emulator import *
from zaber.device.ascii.port.emulator import *
from zaber.device.ascii import *

debug = True

my_metadata = {
    1: {
        'deviceID': 30111,
        'serial': 10000,
        'has_streams':False,
        'peripherals':{
            1: {
                'peripheral_id':21244,
                'serial':00000,
                'has_encoder': True,
                'has_away': False
            }
        }
    },
    2: {
        'deviceID': 22111,
        'serial': 22498,
        'has_streams':False,
        'has_encoder': True,
        'has_away': False
    },
    3: {
        'deviceID': 30221,
        'serial': 28958,
        'has_streams':True,
        'peripherals':{
            1: {
                'peripheral_id':00000,
                'serial':00000,
                'has_encoder': False,
                'has_away': True
            },
            2: {
                'peripheral_id':00001,
                'serial':00000,
                'has_encoder': True,
                'has_away': False
            }
        }
    }
}

settings = {
  'deviceid': 65535,
  'comm.address': 2,
}

device = EmulatorDeviceSingleAxis(
                settings=settings,
                debug=debug
            )

port = PortEmulator(
            devices=[device],
            debug=debug
          )

z = Interface(port=port,custom_metadata=my_metadata)

print(z)

print(z[1].m['deviceID'])

print(z[2].m['deviceID'])
y = z[2]
print(y.m['deviceID'])

print(z[3][1].m['peripheral_id'])

