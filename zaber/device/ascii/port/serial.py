from __future__ import absolute_import

import serial
import zaber.device.ascii.port.base as base

class PortSerial(serial.Serial,base.PortMixin):

    def __init__(self,*args,**kwargs):
        kwargs.setdefault('baudrate',115200)
        kwargs.setdefault('timeout',3)
        self.init(*args,**kwargs)
        super(PortSerial,self).__init__(*args,**kwargs)

    def readline(self,*args,**kwargs):
        response_line = super(PortSerial,self).readline(*args,**kwargs)
        try:
            response_line = str(response_line,'UTF-8')
        except TypeError: pass
        return response_line

