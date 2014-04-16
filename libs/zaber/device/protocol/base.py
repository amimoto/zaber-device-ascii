import re
import zaber.device.port.serial as port

class ZaberProtocol(dict):

    def __init__(self,*args,**kwargs):
        port_class = kwargs.pop('port_class',port.ZaberPortSerial)
        self._port = port_class(*args,**kwargs)

    def devices(self):
        return self.values()
