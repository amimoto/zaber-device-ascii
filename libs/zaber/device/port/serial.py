from __future__ import absolute_import

import serial
import zaber.device.port.base as base

class ZaberPortSerial(serial.Serial,base.ZaberPortMixin):

    def __init__(self,*args,**kwargs):
        self.init(*args,**kwargs)
        super(ZaberPortSerial,self).__init__(*args,**kwargs)

