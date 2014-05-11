from __future__ import absolute_import

import serial
import zaber.device.ascii.port.base as base

class PortSerial(serial.Serial,base.PortMixin):

    def __init__(self,*args,**kwargs):
        kwargs.setdefault('baudrate',115200)
        kwargs.setdefault('timeout',3)
        self.init(*args,**kwargs)
        super(PortSerial,self).__init__(*args,**kwargs)

