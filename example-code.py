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

# Send /renumber
z.renumber()

# Send /renumber THEN /home
z.renumber().home()

# Send /move rel 2000
r = z.move('rel',2000)

# Send also /move rel 2000
r = z.move_rel(2000)

# Send /0 move rel 20000
r = z[0].move_rel(20000)

# Send /0 0 move rel 20000
z[0][0].move_rel(20000)

# Send /0 1 move rel 20000 THEN /0 1 home
z[0][1].move_rel(20000)\
       .home()

# Request a /get accel
r = z.accel

# Do a /set accel <whatever r is>
z.accel = r

# Request /get limit.detect.maxspeed
r = z.limit.detect.maxspeed

# Request /0 get limit.detect.maxspeed
r = z[0].limit.detect.maxspeed

# Reqest /0 0 get limit.detect.maxspeed
r = z[0][0].limit.detect.maxspeed

# Do a /0 0 set limit.detect.maxspeed <whatever r is>
z[0][0].limit.detect.maxspeed = r


