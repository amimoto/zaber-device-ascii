import zaber.device.ascii.port.base as base
from zaber.device.ascii.emulator import *

class ZaberPortEmulator(base.ZaberPortMixin):

    def __init__(self,*args,**kwargs):
        self._engine = EmulatorEngine(**kwargs)
        self._engine.start()

    def read(self,*args,**kwargs):
        return self._engine.read(*args,**kwargs)

    def readline(self,*args,**kwargs):
        return self._engine.readline(*args,**kwargs)

    def write(self,*args,**kwargs):
        return self._engine.write(*args,**kwargs)

    def writeline(self,*args,**kwargs):
        return self._engine.writeline(*args,**kwargs)

