#!/usr/bin/python

from __future__ import print_function

import time

from zaber.device.ascii import *

z = Interface('/dev/ttyUSB0',debug=True)

print(z.autodetect())
print(z[1].s.pos)
print(z[1].help())
time.sleep(0.1)
print(z[1].s.comm.protocol())
print(z[1].s.comm.protocol)
print("Driver Current Run:", z[1].s.driver.current.run)
print("Driver Current Run:", z.s.driver.current.run[1])
z[1].move_vel(1000)
z[1].s.pos = 0
print(z[1].s.pos)
print(z[1].stop())

