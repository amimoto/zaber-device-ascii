import re
import zaber.device.port.serial as port

class ZaberProtocol(dict):

    def __init__(self,*args,**kwargs):
        self._port = kwargs.pop('port',None)
        if not self._port:
            port_class = kwargs.pop('port_class',port.ZaberPortSerial)
            self._port = port_class(*args,**kwargs)

    def devices(self):
        return self.values()
