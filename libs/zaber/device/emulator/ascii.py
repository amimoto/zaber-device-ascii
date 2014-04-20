import time
import datetime
import Queue
import re
import threading
import csv

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
            time_delta_seconds = time_delta.seconds + time_delta.microseconds

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
                if timeout == 0: return
                if timeout <= time_delta_seconds: return
                time.sleep(0.1)


class EmulatorASCIIResponse(dict):
    """
      Responses should have the following parameters:

      :param response_type: response type @, #, or !
      :param address: int or null
      :param scope: int or null
      :param success: if command succeeded. eg. OK
      :param state: axis state eg. IDLE
      :param fault: --
      :param values: array return values
      :param checksum: include checksum. default false

    """

    def __init__(self, 
            response_type='@', 
            address=0, 
            scope=0, 
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
          'address': address,
          'scope': scope,
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
        response_elements.append(str(self.scope))
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
        self['device_address'] = m.group(1)
        self['device_axis'] = m.group(2)
        elements = m.group(3).split(' ',1)
        self['command'] = elements.pop(0).lower() if elements else ''
        self['parameters'] = elements.pop(0).split(' ') if elements else []

    def __str__(self):
        command_str = ""
        command_elements = []
        if self.device_address != None:
            command_elements.append(self.device_address)
            if self.device_axis != None:
                command_elements.append(self.device_axis)
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

class Base(object): pass
class EmulatorASCIIDeviceMotor(Base,threading.Thread):        

    def __init__(self,*args,**kwargs):
        super(EmulatorASCIIDeviceMotor,self).__init__(*args,**kwargs)
        self._settings = kwargs.pop('axis_settings',{})
        self.daemon = True
        self._running = True

        # State of the motor
        self._position_prev = 0
        self._position = 0
        self._position_min = 0
        self._position_max = 305381
        self._velocity = 0
        self._stalled = False

    def motor_velocity(self,*args):
        # FIXME concurrency problem here
        #       read/write to attribs
        if args: self._velocity = args[0]
        return self._velocity

    def motor_position(self):
        # FIXME concurrency problem here
        #       read/write to attribs
        return self._position

    def motor_stop(self):
        self.motor_velocity(0)

    def join(self,timeout=None):
        # FIXME concurrency problem here
        #       read/write to attribs
        self._running = False
        super(EmulatorASCIIDeviceMotor,self).join(timeout)

    def run(self):
        """ Main loop that just runs the "motor"
        """
        time_slice = 0.1
        while self._running == True:
            time.sleep(time_slice)

            position = self._position
            if not self._stalled \
               and position >= self._position_min \
               and position <= self._position_max:
                  delta = int((self._velocity/1.6384)*time_slice)
                  position += delta

            if position < self._position_min: position = self._position_min
            if position > self._position_max: position = self._position_max

            self._position_prev = self._position
            self._position = position

            if self._position != self._position_prev:
                print "MPOS {}".format(self._position)


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


class EmulatorASCIIDevice(Emulator,threading.Thread):
    """
      Represents a device in the system. This part of the code
      handles the basic data stream IO.
    """

    def init_axes(self,args,kwargs):
        pass

    def __init__(self, *args, **kwargs):
        kwargs['call_super'] = True

        self._time_slice = 0.1
        self._clock = 0
        self._settings_config = kwargs.get('settings_config',None)
        self._settings = kwargs.get('settings',{})
        self._running = True
        self.device_address(1)
        self._last_successful_command = None


        self.init_axes(args,kwargs)

        super(EmulatorASCIIDevice,self).__init__(*args,**kwargs)
        self.daemon = True
        self._running = True

    def device_address(self,device_address=None):
        if device_address:
            self._settings['comm.address'] = int(device_address)
        return int(self._settings['comm.address'])

    def start_axes(self):
        pass

    def start(self):
        super(EmulatorASCIIDevice,self).start()
        self.start_axes()

    def join(self,timeout):
        # FIXME concurrency problem here
        #       read/write to attribs
        self._running = False
        super(EmulatorASCIIDevice,self).join(timeout)

    def command_for_me(self,command):
        # Broadcast commands
        if command.device_address in(None,0):
            return True

        # Default reject
        return False

    def respond(self,**kwargs):
        kwargs['address'] = self.device_address()
        response = EmulatorASCIIResponse(**kwargs)
        response_str = str(response)
        self.cable_to_computer().writeline(response_str)

    def setting_get(self, name):
        if name in self._settings:
            return self._settings[name]
        return None

    def setting_set(self, name, value):
        if name in self._settings:
            func_name = 'do_setting_set_'+ name.replace('.','_')
            if hasattr(self,func_name):
                return getattr(self,func_name)(name,value)
            else:
                self._settings[name] = value
                return self._settings[name]
        return None

    def do_command_renumber(self,command):
        if not command.parameters:
            self.device_address(1)
            command.parameters = [2]
        else:
            self.device_address(command.parameters[0])
            command.parameters[0] = self.device_address() + 1
        self.command_relay(command)
        self.respond(values=0)
        return True

    def do_command_(self,command):
        self.command_relay(command)
        self.respond(values=0)
        return True

    def do_command_get(self,command):
        name = command.parameters[0]
        value = self.setting_get(name)
        if value != None:
            self.respond(values=value)
        else:
            self.respond(success='RJ', values='BADCOMMAND')
        self.command_relay(command)

    def do_command_set(self,command):
        name = command.parameters[0]
        value = self.setting_set(name,command.parameters[1])
        if value != None:
            self.respond()
        else:
            self.respond(success='RJ', values='BADCOMMAND')
        self.command_relay(command)

    def do_command_help(self,command):
        self.respond()
        self.respond(response_type='#', values='Thank you Mario! But our princess is in another castle!')
        self.command_relay(command)

    def do_command_l(self,command):
        raise NotImplementedError()
        self.command_relay(command)

    def command_relay(self,command):
        command_str = str(command)
        self.cable_to_device().writeline(command_str)

    def command_execute(self,command):
        # self.cable_to_computer().writeline('@01 0 RJ IDLE WR BADDATA')
        return False

    def command_ingest(self,command_str):
        command = EmulatorASCIICommand(command_str)

        # Ignore the command if not for me and just pass it on
        if self._debug:
            print "RELAY <devid:%s> %s" %(command.device_address, repr(command))
        if not self.command_for_me(command):
            self.command_relay(command)
            return

        target_func = "do_command_" + command.command
        if hasattr( self, target_func ):
            success = getattr(self,target_func)(command)
            return
        else:
            self.respond(success='RJ', values='BADCOMMAND')

        self.command_execute(command) 

    def run(self):
        while self._running:
            action = False

            # Any incoming actions?
            command_str = self.cable_to_computer().readline()
            if command_str:
                self.command_ingest(command_str)
                action = True

            # Any ascending actions?
            response_str = self.cable_to_device().read()
            if response_str:
                self.cable_to_computer().write(response_str)
                action = True

            if not action:
                time.sleep(self._time_slice)
                self._clock += self._time_slice

class EmulatorASCIIDeviceSingleAxis(EmulatorASCIIDevice,threading.Thread):

    def init_axes(self, args, kwargs):
        self._axis_motor = EmulatorASCIIDeviceMotor()

    def do_command_estop(self,command):
        self._axis_motor.motor_velocity(0)
        self.command_relay(command)
        return True

    def do_command_move(self,command):
        move_type = command.parameters[0]
        if move_type == 'vel':
            velocity = int(command.parameters[1])
            self._axis_motor.motor_velocity(velocity)
        else:
            self.respond(success='RJ', values='BADCOMMAND')
        self.command_relay(command)
        return True

    def command_for_me(self,command):
        """
          For single axis devices, only when there's no axis as a target
          or the axis is 0 or 1 will we respond to the request
        """
        for_me = super(EmulatorASCIIDeviceSingleAxis,self).command_for_me(command)
        if for_me: return True

        if int(self.device_address()) != int(command.device_address):
            return False

        if command.device_axis in(0,None,1):
            return True

        return False

    def start_axes(self):
        self._axis_motor.start()


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

class EmulatorASCIIEngine(object):

    def __init__(self,devices,*args,**kwargs):
        self._debug = kwargs.pop('debug',False)
        self._daisychain = EmulatorDaisyChain(devices,debug=self._debug)

    def write(self,*args,**kwargs):
        self._daisychain.write(*args,**kwargs)

    def writeline(self,*args,**kwargs):
        self._daisychain.writeline(*args,**kwargs)

    def read(self,size=None):
        return self._daisychain.read(size)

    def readline(self,timeout=0.1):
        return self._daisychain.readline(timeout=timeout)

    def start(self):
        for device in self._daisychain:
            device.start()

        # Give a bit of time for the devices to spin up
        time.sleep(0.2)

    def port(self):
        return self._daisychain

    def join(self,timeout=None):
        return self._daisychain.join(timeout)

debug = False
device1 = EmulatorASCIIDeviceSingleAxis(debug=debug)
device2 = EmulatorASCIIDeviceSingleAxis(debug=debug)

eng = EmulatorASCIIEngine(devices=[device1,device2],debug=debug)
eng.start()
eng.writeline('/renumber')
#eng.writeline('/')
#eng.writeline('/get comm.address')
#eng.writeline('/set maxspeed 153600')
#eng.writeline('/help')
eng.writeline('/move vel 20000')
time.sleep(1)
eng.writeline('/1 estop')

for i in range(20):
    s = eng.read()
    if s: 
        print "OUTPUT:", s,
    else:
        time.sleep(0.1)

eng.join()
