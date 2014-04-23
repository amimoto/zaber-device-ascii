import zaber.device.port.base as base
from zaber.device.emulator.ascii import *

class ZaberPortEmulatorASCII(base.ZaberPortMixin):

    def __init__(self,*args,**kwargs):
        self._engine = EmulatorASCIIEngine(**kwargs)
        self._engine.start()

    def read(self,*args,**kwargs):
        return self._engine.read(*args,**kwargs)

    def readline(self,*args,**kwargs):
        return self._engine.readline(*args,**kwargs)

    def write(self,*args,**kwargs):
        return self._engine.write(*args,**kwargs)

    def writeline(self,*args,**kwargs):
        return self._engine.writeline(*args,**kwargs)

