#!/usr/bin/python

import sys; sys.path.insert(0, "libs")
from zaber.device.interface import *
from zaber.device.port.dummy import *


z = InterfaceASCII('dummy.txt',port_class=ZaberPortDummy)

r = z.move('rel',2000)
r = z.move_rel(2000)

r = z[0].move_rel(20000)
r = z[0][0].move_rel(20000)
r = z.accel
z.accel = r
r = z.limit.detect.maxspeed
r = z[0].limit.detect.maxspeed
r = z[0][0].limit.detect.maxspeed


z[0][0].limit.detect.maxspeed = r

print r
print z

#z = ZaberProtocolASCII('/dev/ttyUSB0',9600)
#r = z.home()
#r = z.move('rel',2000)
#z.renumber()

