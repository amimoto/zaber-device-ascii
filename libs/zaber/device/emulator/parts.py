import Queue
from zaber.device.emulator.base import *

class EmulatorSerialCableEnd(EmulatorReadWritelineBase):
    """
      Create an abstract IO port interface using event
      queues.
    """
    def __init__(self,queue_in,queue_out,*args,**kwargs):
        super(EmulatorSerialCableEnd,self).__init__(*args,**kwargs)
        self._queue_in = queue_in
        self._queue_out = queue_out
        self._read_buffer = ''

    def read(self,size=None):
        if size == None: size = self._read_chunk
        while True:
            try:
                data = self._queue_in.get_nowait()
            except Queue.Empty:
                data = None
            if not data:
                data = ''
                break
            if self._debug:
                print "RD<{}> {}".format(self._id,repr(data))
            self._read_buffer += data

        return_data = self._read_buffer[:size]
        self._read_buffer = self._read_buffer[size:]

        return return_data

    def write(self,data):
        self._queue_out.put(data)

class EmulatorSerialCable(object):
    """
      Creates a dual ended pipe for communication.
      Has two properties after instantiation. 
      port1 and port2 which can communicate to each 
      other using basic read/readline/write/writeline 
      methods.
    """

    def __init__(self,*args,**kwargs):
        self._queue1 = Queue.Queue()
        self._queue2 = Queue.Queue()
        self.port1 = EmulatorSerialCableEnd(self._queue1,self._queue2,*args,**kwargs)
        self.port2 = EmulatorSerialCableEnd(self._queue2,self._queue1,*args,**kwargs)



class EmulatorDaisyChain(list,EmulatorReadWritelineBase):
    """
      Represents a 1-dimensional string of devices strung together.
      This will accept a list of devies (in-order) and tie them
      together with virtual cables.
    """

    def __init__(self,*args,**kwargs):
        debug = kwargs.pop('debug',False)

        super(EmulatorDaisyChain,self).__init__(*args,**kwargs)

        self._debug = debug

        # Create the cable that "goes to the computer" which
        # the system will talk to the devices with
        self._cables = []
        computer_cable = EmulatorSerialCable(debug=self._debug)
        self.port(computer_cable.port1)

        # Connect the cable to the first device in the chain
        dev_prev = self[0]
        dev_prev.cable_to_computer(computer_cable.port2)

        # Connect the rest of the devices
        for dev in self[1:]:
            cable = EmulatorSerialCable(debug=self._debug)
            self._cables.append(cable)
            dev_prev.cable_to_device(cable.port1)
            dev.cable_to_computer(cable.port2)
            dev_prev = dev

    def port(self,port=None):
        if port:
            self._computer_port = port
        return self._computer_port

    def write(self,*args,**kwargs):
        return self.port().write(*args,**kwargs)

    def writeline(self,*args,**kwargs):
        return self.port().writeline(*args,**kwargs)

    def read(self,*args,**kwargs):
        return self.port().read(*args,**kwargs)

    def readline(self,*args,**kwargs):
        return self.port().readline(*args,**kwargs)

    def start(self):
        for dev in self:
            dev.start()

    def join(self,timeout=None):
        for dev in self:
            dev.join(timeout)


