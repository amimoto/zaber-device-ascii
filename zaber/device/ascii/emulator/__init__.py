import re
import datetime
import time
import threading
import os
import csv
import time

import Queue

import zaber.device.ascii

CABLE_COUNTER = 1

ascii_device_default_config = {
                'comm.address': '0',
                'comm.alert': '0',
                'comm.checksum': '0',
                'comm.protocol': '0',
                'comm.rs232.baud': '0',
                'comm.rs232.protocol': '0',
                'comm.rs485.baud': '0',
                'comm.rs485.enable': '0',
                'comm.rs485.protocol': '0',
                'comm.usb.protocol': '0',
                'deviceid': '65535',
                'system.access': '0',
                'system.axiscount': '0',
                'system.current': '0',
                'system.led.enable': '0',
                'system.temperature': '0',
                'system.voltage': '0',
                'version': '0'
            }


ascii_axis_default_config = {
                'accel': '0',
                'cloop.counts': '0',
                'cloop.mode': '0',
                'cloop.stalltimeout': '0',
                'cloop.steps': '0',
                'driver.current.hold': '0',
                'driver.current.run': '0',
                'driver.dir': '0',
                'driver.temperature': '0',
                'encoder.count': '0',
                'encoder.dir': '0',
                'encoder.filter': '0',
                'encoder.index.count': '0',
                'encoder.index.mode': '0',
                'encoder.index.phase': '0',
                'encoder.mode': '0',
                'knob.dir': '0',
                'knob.distance': '0',
                'knob.enable': '0',
                'knob.maxspeed': '0',
                'knob.mode': '0',
                'knob.speedprofile': '0',
                'limit.approach.accel': '0',
                'limit.approach.maxspeed': '153600',
                'limit.away.action': '0',
                'limit.away.edge': '0',
                'limit.away.posupdate': '0',
                'limit.away.preset': '0',
                'limit.away.state': '0',
                'limit.away.triggered': '0',
                'limit.away.type': '0',
                'limit.c.action': '0',
                'limit.c.edge': '0',
                'limit.c.pos': '0',
                'limit.c.posupdate': '0',
                'limit.c.preset': '0',
                'limit.c.state': '0',
                'limit.c.triggered': '0',
                'limit.c.type': '0',
                'limit.d.action': '0',
                'limit.d.edge': '0',
                'limit.d.pos': '0',
                'limit.d.posupdate': '0',
                'limit.d.preset': '0',
                'limit.d.state': '0',
                'limit.d.triggered': '0',
                'limit.d.type': '0',
                'limit.detect.decelonly': '0',
                'limit.detect.maxspeed': '0',
                'limit.home.action': '0',
                'limit.home.edge': '0',
                'limit.home.posupdate': '0',
                'limit.home.preset': '0',
                'limit.home.state': '0',
                'limit.home.triggered': '0',
                'limit.home.type': '0',
                'limit.max': '305381',
                'limit.min': '0',
                'limit.swapinputs': '0',
                'maxspeed': '0',
                'motion.accelonly': '0',
                'motion.decelonly': '0',
                'peripheralid': '0',
                'pos': '0',
                'resolution': '0'
          }


class EmulatorDeviceAxis(threading.Thread):        

    def __init__(self,*args,**kwargs):
        position = kwargs.pop('pos',0)
        self._axis_number = kwargs.pop('axis_number')

        # Load up some of the settings before we hand over kwargs
        # to thread. (Thread will complain about unexpected parameters
        # otherwise)
        self._settings = kwargs.pop('settings')
        self._axis_settings = ascii_axis_default_config.copy()
        self._axis_settings.update(kwargs.pop('axis_settings'))

        # Resolution of the emulation. Smaller the time slice, more
        # granular... but it also costs more CPU time
        self._time_slice = kwargs.pop('time_slice',0.1)

        super(EmulatorDeviceAxis,self).__init__(*args,**kwargs)
        self.daemon = True
        self._running = True

        # State of the motor
        self._real_position_prev = int(self._axis_settings['pos'])
        self._real_position = int(self._axis_settings['pos'])
        self._real_position_min = int(self._axis_settings['limit.min'])
        self._real_position_max = int(self._axis_settings['limit.max'])

        self._assumed_position_prev = int(self._axis_settings['pos'])
        self._assumed_position = int(self._axis_settings['pos'])

        self._velocity = 0
        self._moving = False
        self._stalled = False

    def setting_get(self, name):
        func_name = 'do_setting_get_'+ name.replace('.','_')
        if hasattr(self,func_name):
            return int(getattr(self,func_name)(name,value))
        return int(self._axis_settings.get(name,0))

    def setting_set(self, name, value):
        func_name = 'do_setting_set_'+ name.replace('.','_')
        if hasattr(self,func_name):
            return getattr(self,func_name)(name,value)
        self._axis_settings[name] = value
        return self._axis_settings[name]

    def moving(self):
        if self._velocity == 0:
            return False
        return True

    def moving(self):
        """ The 'moving' flag is based upon the assumed position
            of the device
        """
        if not self._velocity: 
            return False
        if self._assumed_position <= self._real_position_min \
            and self._velocity < 0:
                return False
        if self._assumed_position >= self._real_position_max \
            and self._velocity > 0:
                return False
        return True

    def motor_velocity(self,*args):
        if args: self._velocity = args[0]
        return self._velocity

    def motor_real_position(self):
        return self._real_position

    def motor_stop(self):
        self.motor_velocity(0)

    def join(self,timeout=None):
        self._running = False
        super(EmulatorDeviceAxis,self).join(timeout)

    def move_within_range(self,position,delta):
        """ Given a start position and a delta,
            returns how far the system would allow
            it to go
        """
        position_new = position + delta

        if position_new < self._real_position_min: 
            position_new = self._real_position_min
        if position_new > self._real_position_max: 
            position_new = self._real_position_max

        return position_new

    def axis_move(self):
        """ This initial code simply performs the current
            move requirements without considering the position
            of the physical stage. (This is a base class that
            emulates an axis without an encoder)
        """
        delta = int((self._velocity/1.6384)*self._time_slice)

        # We handle the physical movements separately than the
        # virtual movements

        # Handle the virtual movements
        assumed_position_new = self.move_within_range(self._assumed_position,delta)
        assumed_delta = assumed_position_new - self._assumed_position
        self._assumed_position_prev = self._assumed_position
        self._assumed_position = assumed_position_new
        self._axis_settings['pos'] = assumed_position_new
        self._moving = assumed_delta != 0

        # Handle the real movements
        real_position_new = self.move_within_range(self._real_position,assumed_delta)
        self._real_position_prev = self._real_position
        self._real_position = real_position_new

    def run(self):
        """ Main loop that just runs the "motor"
        """
        while self._running == True:
            time.sleep(self._time_slice)

            # Perform the actions required to move the axis
            self.axis_move()

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

            # Reset the timeout timer if we get some data
            # This means that as long as data is flowing, we'll
            # keep receiving (until we hit a newline)
            if buf:
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



class EmulatorResponse(dict):
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

        super(EmulatorResponse, self).__init__({
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
        # From https://www.zaber.com/wiki/Manuals/_Protocol_Manual#Python
        c_sum = 0
        for c in msg[1:]:
            c_sum += ord(c)                  #calculate the sum of the message to be transmitted
            c_sum = 256 - (c_sum & 0xFF)     #take the ones compliment (negate)
        return '%s:%02X' % (msg, c_sum)  #return the full message


    def __str__(self):
        response_str = self.type
        response_elements = []
        response_elements.append("{:02}".format(int(self.address)))
        response_elements.append(str(self.axis or 0))
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



class EmulatorCommand(dict):

    def __init__(self, command_str, *args, **kwargs):
        super(EmulatorCommand, self).__init__(*args, **kwargs)
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




class EmulatorDevice(Emulator,threading.Thread):
    """
      Represents a device in the system. This part of the code
      handles the basic data stream IO.
    """

    def init_axes(self,args,kwargs):
        pass

    def settings_load(self,settings_config=None,settings=None):
        if settings_config == None:
            base_path = os.path.dirname(zaber.device.ascii.__file__)
            settings_config = os.path.join(base_path,"data","ascii-settings.csv")
        csv_reader = csv.DictReader(open(settings_config))
        settings_data = {}
        for entry in csv_reader:
            settings_data[entry['setting']] = entry
        self._settings_data = settings_data

    def __init__(self, *args, **kwargs):
        kwargs['call_super'] = True

        self._time_slice = 0.1
        self._clock = 0

        self._settings_config = kwargs.get('settings_config',None)
        self._settings = ascii_device_default_config.copy()
        self._settings.update(kwargs.pop('settings',{}))
        self.settings_load(self._settings_config,self._settings)

        self._running = True
        self._last_successful_command = None

        self.init_axes(args,kwargs)

        super(EmulatorDevice,self).__init__(*args,**kwargs)
        self.daemon = True

    def address(self,address=None):
        if address:
            self._settings['comm.address'] = int(address)
        return int(self._settings['comm.address'])

    def start_axes(self):
        pass

    def start(self):
        super(EmulatorDevice,self).start()
        self.start_axes()

    def join(self,timeout):
        # FIXME concurrency problem here
        #       read/write to attribs
        self._running = False
        super(EmulatorDevice,self).join(timeout)

    def command_for_me(self,command):
        # Broadcast commands
        if command.address in(None,0):
            return True

        # Default reject
        return False

    def respond(self,**kwargs):
        kwargs['address'] = self.address()
        response = EmulatorResponse(**kwargs)
        response_str = str(response)
        self.cable_to_computer().writeline(response_str)

    def setting_get(self, name):
        if name in self._settings_data:
            if self._settings_data[name]['scope'] == 'axis':
                return None
            func_name = 'do_setting_get_'+ name.replace('.','_')
            if hasattr(self,func_name):
                return getattr(self,func_name)(name,value)
            else:
                return self._settings.get(name,0)
        return None

    def setting_set(self, name, value):
        if name in self._settings_data:
            func_name = 'do_setting_set_'+ name.replace('.','_')
            if self._settings_data[name]['scope'] == 'axis':
                return None
            if self._settings_data[name]['writable'] != 'yes':
                return None
            if hasattr(self,func_name):
                return getattr(self,func_name)(name,value)
            elif self._settings_data[name]['writable'] == 'yes':
                self._settings[name] = value
                return self._settings[name]
        return None

    def do_command_renumber(self,command):
        address_new = int(command.parameters[0]) \
                          if command.parameters \
                          else 1
        address_new += ord(command.command[7])-0x80
        self.address(address_new)
        self.respond(values=0)
        return True

    def position_stats(self):
        return {
            
        }

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

    def do_command_home(self,command):
        maxspeed = int(self.setting_get('limit.approach.maxspeed'))
        if command.axis:
            self._axes_objects[command.axis - 1].motor_velocity(-maxspeed)
        else:
            for obj in self._axes_objects:
                obj.motor_velocity(-maxspeed)
        self.respond(axis=command.axis)

    def do_command_help(self,command):
        self.respond()
        self.respond(
                response_type='#', 
                values='Thank you Mario! But our '\
                        +'princess is in another castle!')

    def do_command_l(self,command):
        raise NotImplementedError()

    def command_relay(self,command):
        command_str = str(command)
        if self._debug:
            print "RELAY <devid:%s> %s" %(command.address, repr(command))
        self.cable_to_device().writeline(command_str)

    def command_execute(self,command):
        # self.cable_to_computer().writeline('@01 0 RJ IDLE WR BADDATA')
        return False

    def command_ingest(self,command_str):
        """
          We've received a command. We'll forward all commands except
          for the renumber command where we'll do something tricky.
        """

        command = EmulatorCommand(command_str)

        # So for renumber, we do some tricky stuff.
        # This: /renumber ...
        # After the first device becomes
        # Becomes: /renumbeX ...
        # Where X = chr(0x80)
        # After the subsequent devices, X = X+1, so
        # So after the second device, it's
        # Becomes: /renumbeX ...
        # Where X = chr(0x80)
        if re.search('^renumb.',command.command):
            command_new = list(command.command)
            char_new = ord(command_new[7])
            char_new = 0x80 if char_new == 0x72 \
                            else char_new + 1
            command_new[7] = chr(char_new)
            command.command = "".join(command_new)
            self.command_relay(command)
            self.do_command_renumber(command)
            return

        # Relay the command by default (except for renumber)
        self.command_relay(command)

        # Ignore the command if not for me
        if not self.command_for_me(command): return

        if self._debug:
            print "DEV<{}> Command for me. {}".format(self.address(),command_str)

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

            # If nothing happened, wait a moment.
            if not action:
                time.sleep(self._time_slice)
                self._clock += self._time_slice

class EmulatorDeviceAxes(EmulatorDevice,threading.Thread):

    _axis_count = 0

    def init_axes(self, args, kwargs):

        self._axes_objects = []
        self._settings.setdefault('axes_settings',[])
        axes_settings = self._settings['axes_settings']

        for i in range(self._axis_count):
            if len(axes_settings) <= (i+1):
                axes_settings.append({})
            axis_settings = axes_settings[i]
            self._axes_objects.append(
                EmulatorDeviceAxis(
                    axis_number=i+1,
                    settings=self._settings,
                    axis_settings=axis_settings
                )
            )

        self._settings['system.axiscount'] = self._axis_count

    def respond(self,**kwargs):
        kwargs['state'] = 'IDLE'
        for obj in self._axes_objects:
            if obj.moving():
                kwargs['state'] = 'BUSY'
                break
        return super(EmulatorDeviceAxes,self).respond(**kwargs)

    def setting_get(self, name):
        result = super(EmulatorDeviceAxes,self).setting_get(name)
        if result: return result

        if not name in self._settings_data:
            return None

        if self._settings_data[name]['scope'] != 'axis':
            return None

        values = []
        for obj in self._axes_objects:
            values.append(obj.setting_get(name) or 0)

        if values:
            return " ".join([str(i) for i in values])

        return None

    def setting_set(self, name, value):
        result = super(EmulatorDeviceAxes,self).setting_set(name,value)
        if result: return result

        if not name in self._settings_data:
            return None

        if self._settings_data[name]['scope'] != 'axis':
            return None

        if self._settings_data[name]['writable'] != 'yes':
            return None

        values = []
        for obj in self._axes_objects:
            values.append(obj.setting_set(name,value) or 0)

        if values:
            return " ".join([str(i) for i in values])

        return None

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
        for_me = super(EmulatorDeviceAxes,self).command_for_me(command)
        if for_me: return True

        if int(self.address()) != int(command.address):
            return False

        if command.axis in(0,None,1):
            return True

        return False

    def start_axes(self):
        for obj in self._axes_objects:
            obj.start()

class EmulatorDeviceSingleAxis(EmulatorDeviceAxes):
    _axis_count = 1

class EmulatorEngine(object):

    def __init__(self,devices,*args,**kwargs):
        self._debug = kwargs.pop('debug',False)
        self._daisychain = EmulatorDaisyChain(devices,debug=self._debug)

    def write(self,*args,**kwargs):
        self._daisychain.write(*args,**kwargs)

    def writeline(self,*args,**kwargs):
        self._daisychain.writeline(*args,**kwargs)

    def read(self,*args,**kwargs):
        return self._daisychain.read(*args,**kwargs)

    def readline(self,*args,**kwargs):
        return self._daisychain.readline(*args,**kwargs)

    def start(self):
        for device in self._daisychain:
            device.start()

        # Give a bit of time for the devices to spin up
        time.sleep(0.2)

    def port(self):
        return self._daisychain

    def join(self,timeout=None):
        return self._daisychain.join(timeout)



