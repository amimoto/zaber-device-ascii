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

# We could use autodetect but that slows the script execution down.
# Instead, we know that the emulated layout of the device is as follows
# so we can pass the layout metadata directly
devices = {1: {'axiscount': 1, 'deviceid': 65535, 'address': 1}}

z = InterfaceASCIIHelpers(port=port,devices=devices)

print "--------------------------------------------------"
print "Sending device 1 axis 1 to home"
print "--------------------------------------------------"

#z.home().w().move_rel(20000)

print "--------------------------------------------------"
print "Starting to checking position of devices"
print "--------------------------------------------------"

for i in range(1000):

    """
    When requests are sent, one device will send just one 
    response. This is regardless of the format of the command 
    and the number of axes.

    So a command line

    /get 1 0 pos

    Will return something like

    @01 0 OK IDLE -- 10000:D8

    If it has two axes, it may look like:

    @01 0 OK IDLE -- 10000 10000

    So in code, that will be represented by:

    response = z.pos

    To access the first device, one would use the format:

    response[1]

    However, what about the first axis?

    response[1][1]

    Would seem natural.

    However, there's a small problem.

    There are two types of settings: Device and axis

    An example of a device level setting would be deviceid

    It would make sense to be able to do something like:

    print z[1].deviceid
    print z.deviceid[1]

    However, also be able to do something like:

    print z[1][1].pos
    print z[1].pos[1]
    print z.pos[1][1]

    It would also be nice to be able to do something like:

    for addr_id,addr_data in z.pos.iteritems():
       for axis_num,axis_data in addr_data.iteritems():
         print "Device Addr", addr_id, \
                "Axis", axis_num, \
                "Position:", axis_data

    What should happen if someone tries to do this?

    print z[1][1].deviceid
    print z.deviceid[1][1]

    Throw warning? Fatal? Or silently accomodate?

    If this is sent to a device, it would fail:

    /1 1 get deviceid

    While this would be okay:

    /1 0 get deviceid

    We already have a csv database of all the keys available
    so should we take advantage of this to determine additional info?

    Probably should throw an error?

    """

    print "--------------------------------------------------"
    print "This should return something like {1:{1:1000}}"
    print "--------------------------------------------------"
    print z.pos

    print "--------------------------------------------------"
    print "This should return something like {1:1000}"
    print "--------------------------------------------------"
    print z.pos[1]
    print z[1].pos

    print "--------------------------------------------------"
    print "This should return something like 1000"
    print "--------------------------------------------------"
    print z.pos[1][1]
    print z[1].pos[1]
    print z[1][1].pos

    print "--------------------------------------------------"
    print "This should return something like 65535"
    print "--------------------------------------------------"
    print z[1].deviceid

    import pdb; pdb.set_trace()
    time.sleep(0.1)

