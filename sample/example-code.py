#!/usr/bin/python

import time

from zaber.device.ascii.emulator import *
from zaber.device.ascii.port.emulator import *
from zaber.device.ascii import *

debug=True

# Create a single axis emulated device
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

# Subclassing zaber.device.port.base.ZaberPortMixin will
# allow you to create custom serial interfaces, such as
# the dummy "load responses from text" interface. Normally
# it'd go to the serial port. However, you can create one for
# a TCPIP socket quite easily as well
z = Interface(port=port,debug=debug)

# Normally, the following would be good enough:
# z = Interface('/dev/ttyUSB0')

# Basic: Send /renumber
# Note: that because we're sending out a broadcast request, we have to send it manually
z.request('renumber')

# Commands with parameters: Send /move rel 2000
r = z[1].move('rel',2000)

# Display of response
print "Type", r.message_type
print "Addr", r.address
print "Axis", r.axis
print "Reply Flags", r.reply_flags
print "Warn Flags", r.warn_flags
print "Status", r.status
print "Message", r.message

# Command names can also hide parameters: Send also /1 move rel 2000
r = z[1].move_rel(2000)

# Indexing for Axes: Send /1 1 move rel 20000
z[1][1].move_rel(20000)

# Command chain/indexing abuse:
# Send:
# /1 1 set maxspeed 1000
# /1 1 move rel 20000 
# /1 1 set maxspeed 9001
# /1 1 home
# TODO: Include poll until idle command
#       Probably would be like .poll()
z[1][1].set_maxspeed(1000)\
        .move_rel(20000)\
        .set_maxspeed(9001)\
        .home()\

# Setting fetch: Request a /1 get accel
r = z[1].s.accel

# Setting set: Do a /set accel <whatever r is>
z[1].s.accel = r

# Setting with periods: Request /1 get limit.detect.maxspeed
# Note that the response is lazy eval'd, the request to the device 
# goes out when it's required. It's kinda bad that it does it every 
# time though. Thinking about the best way of handling this one
# still
r = z[1].s.limit.detect.maxspeed
print r

# Settings with indexing: Reqest /1 1 get limit.detect.maxspeed
r = z[1][1].s.limit.detect.maxspeed
print r

# Set settings with indexing: Do a /1 1 set limit.detect.maxspeed <whatever r is>
z[1][1].s.limit.detect.maxspeed = r


