import zaber.device.port.serial as port
import zaber.device.protocol.ascii as protocol


# Device map

class InterfaceASCII(dict):

    def __init__(self,*args,**kwargs):
        port_class = kwargs.pop('port_class',port.ZaberPortSerial)
        protocol_class = kwargs.pop('protcol_class',protocol.ZaberProtocolASCII)
        kwargs['port_class'] = port_class
        self._protocol = protocol_class(*args,**kwargs)
        self.probe()

    def probe(self):
        devices = self._protocol.enumerate()

    def __getattr__(self,k):
        if k in self._protocol:
            return lambda *args,**kwargs: self._protocol.request(k,*args,**kwargs)
        raise AttributeError(
                "'{}' object has no attribute '{}'".format(type(self).__name__,k)
              )




