#!/usr/bin/python

import sys; sys.path.insert(0, "lib")
from zaber.device.interface import *
import zaber.device.port.dummy


z = InterfaceASCII('dummy.txt',port_class=zaber.device.port.dummy.ZaberPortDummy)

#z = ZaberProtocolASCII('dummy.txt',port_class=zaber.device.port.dummy.ZaberPortDummy)
r = z.move_rel(2000)
print r
print z

#z = ZaberProtocolASCII('/dev/ttyUSB0',9600)
#r = z.home()
#r = z.move('rel',2000)
#z.renumber()

