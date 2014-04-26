import re
import datetime
import time

CABLE_COUNTER = 1

def cable_counter():
    global CABLE_COUNTER
    _id = CABLE_COUNTER 
    CABLE_COUNTER += 1
    return _id
    

class EmulatorReadWritelineSink(object):
    def write(self,*args,**kwargs):
        pass
    def writeline(self,*args,**kwargs):
        pass
    def read(self,*args,**kwargs):
        return
    def readline(self,*args,**kwargs):
        return

class EmulatorReadWritelineBase(object):

    def __init__(self, *args, **kwargs):
        self._debug = kwargs.pop('debug', False)
        self._read_chunk = kwargs.pop('read_chunk',4096)
        self._buffer = ''
        self._id = cable_counter()

    def write(self,*args,**kwargs):
        pass

    def writeline(self,data,*args,**kwargs):
        if self._debug:
            print "WRLN<{}> {}".format(self._id, repr(data))
        self.write(data+"\r\n",*args,**kwargs)

    def read(self,*args,**kwargs):
        pass

    def readline(self,timeout=0,*args,**kwargs):
        start_time = datetime.datetime.now()
        while True:
            buf = self.read(self._read_chunk,*args,**kwargs)
            time_delta = datetime.datetime.now() - start_time
            time_delta_seconds = time_delta.seconds + time_delta.microseconds/1000000.000 

            self._buffer += buf or ''

            start_time = datetime.datetime.now()

            m = re.search('^(.*?)\r?\n(.*)',self._buffer,re.S)
            if m:
                self._buffer = m.group(2)
                if self._debug:
                    print "RDLN<{}> {} buffer:{}".format( 
                              self._id, 
                              repr(m.group(1)), 
                              repr(self._buffer) )
                return m.group(1)
            else:
                if timeout == 0: 
                    return
                elif timeout < 0: 
                    time.sleep(0.1)
                elif timeout <= time_delta_seconds: 
                    return
                else:
                    time.sleep(0.1)



class EmulatorASCIIResponse(dict):
    """
      Responses should have the following parameters:

      :param response_type: response type @, #, or !
      :param address: int or null
      :param axis: int or null
      :param success: if command succeeded. eg. OK
      :param state: axis state eg. IDLE
      :param fault: --
      :param values: array return values
      :param checksum: include checksum. default false

    """

    def __init__(self, 
            response_type='@', 
            address=0, 
            axis=0, 
            success='OK', 
            state='IDLE', 
            fault='--', 
            values=[0],
            checksum=True
        ):

        if type(values) is not list:
            values = [values]

        super(EmulatorASCIIResponse, self).__init__({
          'type': response_type,
          'address': None if address == None else int(address),
          'axis': None if axis == None else int(axis),
          'success': success,
          'state': state,
          'fault': fault,
          'values': values,
          'checksum': checksum
        })
        self.__dict__ = self

    def csum_message(self,msg):
        # From https://www.zaber.com/wiki/Manuals/ASCII_Protocol_Manual#Python
        c_sum = 0
        for c in msg[1:]:
            c_sum += ord(c)                  #calculate the sum of the message to be transmitted
            c_sum = 256 - (c_sum & 0xFF)     #take the ones compliment (negate)
        return '%s:%02X' % (msg, c_sum)  #return the full message


    def __str__(self):
        response_str = self.type
        response_elements = []
        response_elements.append("{:02}".format(int(self.address)))
        response_elements.append(str(self.axis))
        if self.type == '@':
            response_elements += [
                self.success,
                self.state,
                self.fault,
            ]
        elif self.type == '#':
            pass

        response_str += " ".join([str(e) for e in response_elements+self.values])

        if self.checksum:
            return self.csum_message(response_str)

        return response_str

class EmulatorASCIICommand(dict):

    def __init__(self, command_str, *args, **kwargs):
        super(EmulatorASCIICommand, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.command_parse(command_str)

    def command_parse(self,command_str):
        m = re.search('^\s*/(?:(\d+)\s+(?:(\d+)\s+)?)?(.*)',command_str)
        address = m.group(1)
        axis = m.group(2)
        self['address'] = None if address == None else int(address)
        self['axis'] = None if axis == None else int(axis)
        elements = m.group(3).split(' ',1)
        self['command'] = elements.pop(0).lower() if elements else ''
        self['parameters'] = elements.pop(0).split(' ') if elements else []

    def __str__(self):
        command_str = ""
        command_elements = []
        if self.address != None:
            command_elements.append(str(self.address))
            if self.axis != None:
                command_elements.append(str(self.axis))
        command_elements.append(self.command)

        parameters = [str(p) for p in self.parameters]
        command_elements += parameters
        return "/"+(" ".join(command_elements))




class Emulator(object):
    def __init__(self,*args,**kwargs):
        self._debug = kwargs.pop('debug',False)

        if kwargs.pop('call_super'):
            super(Emulator,self).__init__(*args,**kwargs)

        self._port_to_computer = kwargs.get(
                                    'port_to_computer',
                                    EmulatorReadWritelineSink()
                                )
        self._port_to_device = kwargs.get(
                                  'port_to_device',
                                  EmulatorReadWritelineSink()
                                )

    def cable_to_computer(self,port=None):
        """ 
          Connect the device to a new cable that 
          eventually ends up at the "computer"
        """
        if port != None:
            self._port_to_computer = port
        return self._port_to_computer

    def cable_to_device(self,port=None):
        """
          Connect the device to a new cable that
          goes towards the next device in the chain
        """
        if port != None:
            self._port_to_device = port
        return self._port_to_device



