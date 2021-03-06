from __future__ import absolute_import

import zaber.device.ascii.port.base as base

class PortDummy(file,base.PortMixin):

    def readline(self):
        line = super(PortDummy,self).readline()

        # If "delay" is put into the text file, it will
        # fake a pause in the response
        if line[:5] == 'delay':
            return

        return line

    def write(self,data):
        print "WRITE:", data

    def writeline(self,data):
        print "WRITELINE:", data

    def __init__(self,*args,**kwargs):
        self.init(*args,**kwargs)
        super(PortDummy,self).__init__(*args,**kwargs)

