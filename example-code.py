#!/usr/bin/python

import sys; sys.path.insert(0, "libs")
from zaber.device.interface import *
from zaber.device.port.dummy import *

# Subclassing zaber.device.port.base.ZaberPortMixin will
# allow you to create custom serial interfaces, such as
# the dummy "load responses from text" interface. Normally
# it'd go to the serial port. However, you can create one for
# a TCPIP socket quite easily as well
z = InterfaceASCII('dummy.txt',port_class=ZaberPortDummy)

# Normally, the following would be good enough:
# z = InterfaceASCII('/dev/ttyUSB0')

# Basic: Send /renumber
z.renumber()

# Chaining: Send /renumber THEN /home
z.renumber().home()

# Commands with parameters: Send /move rel 2000
r = z.move('rel',2000)

# Display of response
print "Type", r.message_type
print "Addr", r.address
print "Axis", r.axis
print "Reply Flags", r.reply_flags
print "Warn Flags", r.warn_flags
print "Status", r.status
print "Message", r.message

# Command names can also hide parameters: Send also /move rel 2000
r = z.move_rel(2000)

# Indexing for devices: Send /0 move rel 20000
r = z[0].move_rel(20000)

# Indexing for Axes: Send /0 0 move rel 20000
z[0][0].move_rel(20000)

# Command chain/indexing abuse:
# Send:
# /0 1 set maxspeed 1000
# /0 1 move rel 20000 
# /0 1 set maxspeed 9001
# /0 1 home
# TODO: Include poll until idle command
#       Probably would be like .poll()
z[0][1].set_maxspeed(1000)\
        .move_rel(20000)\
        .set_maxspeed(9001)\
        .home()\

# Setting fetch: Request a /get accel
r = z.accel

# Setting set: Do a /set accel <whatever r is>
z.accel = r

# Setting with periods: Request /get limit.detect.maxspeed
# Note that the response is lazy eval'd, the request to the device 
# goes out when it's required. It's kinda bad that it does it every 
# time though. Thinking about the best way of handling this one
# still
r = z.limit.detect.maxspeed
print r

# Settings with indexing: Request /0 get limit.detect.maxspeed
r = z[0].limit.detect.maxspeed
print r

# Settings with indexing: Reqest /0 0 get limit.detect.maxspeed
r = z[0][0].limit.detect.maxspeed
print r

# Set settings with indexing: Do a /0 0 set limit.detect.maxspeed <whatever r is>
z[0][0].limit.detect.maxspeed = r


