import re

class ZaberPortMixin(object):
    """ Abstraction allows future extension of the port interface
        to allow bridging via IP/nordic/etc protocols
    """

    def init(self,*args,**kwargs):
        self._buffer = ''
        self._read_chunk = kwargs.get('read_chunk') or 4096
        self._timeout = kwargs.get('timeout') or None

    def read(self,size):
        raise NotImplementedError

    def readline(self,timeout=None):
        if timeout == None:
            timeout = self._timeout

        while True:
            buf = self.read(self._read_chunk)
            if buf == None:
                if timeout < 0: continue
                return
            self._buffer += buf
            m = re.search('^(.*?)\r?\n(.*)',self._buffer,re.S)
            if m:
                self._buffer = m.group(2)
                return m.group(1)

    def write(self,data):
        raise NotImplementedError

    def writeline(self,data):
        return self.write(data+"\r\n")

