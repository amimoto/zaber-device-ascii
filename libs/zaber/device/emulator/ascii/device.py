import threading
import os
import csv
import time

import zaber.device
from zaber.device.emulator.base import *
from zaber.device.emulator.parts import *

from zaber.device.emulator.ascii.axes import *

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

class EmulatorASCIIDevice(Emulator,threading.Thread):
    """
      Represents a device in the system. This part of the code
      handles the basic data stream IO.
    """

    def init_axes(self,args,kwargs):
        pass

    def settings_load(self,settings_config=None,settings=None):
        if settings_config == None:
            base_path = os.path.dirname(zaber.device.__file__)
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
        self.address(1)
        self._last_successful_command = None

        self.init_axes(args,kwargs)

        super(EmulatorASCIIDevice,self).__init__(*args,**kwargs)
        self.daemon = True

    def address(self,address=None):
        if address:
            self._settings['comm.address'] = int(address)
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
        if command.address in(None,0):
            return True

        # Default reject
        return False

    def respond(self,**kwargs):
        kwargs['address'] = self.address()
        response = EmulatorASCIIResponse(**kwargs)
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

        command = EmulatorASCIICommand(command_str)

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

class EmulatorASCIIDeviceAxes(EmulatorASCIIDevice,threading.Thread):

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
                EmulatorASCIIDeviceAxis(
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
        return super(EmulatorASCIIDeviceAxes,self).respond(**kwargs)

    def setting_get(self, name):
        result = super(EmulatorASCIIDeviceAxes,self).setting_get(name)
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
        result = super(EmulatorASCIIDeviceAxes,self).setting_set(name,value)
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
        for_me = super(EmulatorASCIIDeviceAxes,self).command_for_me(command)
        if for_me: return True

        if int(self.address()) != int(command.address):
            return False

        if command.axis in(0,None,1):
            return True

        return False

    def start_axes(self):
        for obj in self._axes_objects:
            obj.start()


class EmulatorASCIIDeviceSingleAxis(EmulatorASCIIDeviceAxes):
    _axis_count = 1


class EmulatorASCIIEngine(object):

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



