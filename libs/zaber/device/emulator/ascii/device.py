import threading
import os
import csv
import time

import zaber.device
from zaber.device.emulator.base import *
from zaber.device.emulator.parts import *

from zaber.device.emulator.ascii.axes import *

class EmulatorASCIIDevice(Emulator,threading.Thread):
    """
      Represents a device in the system. This part of the code
      handles the basic data stream IO.
    """

    def init_axes(self,args,kwargs):
        pass

    def settings_load(self,settings_config=None):
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
        self.settings_load(self._settings_config)

        self._settings = kwargs.get('settings',{})
        self._running = True
        self.device_address(1)
        self._last_successful_command = None

        self.init_axes(args,kwargs)

        super(EmulatorASCIIDevice,self).__init__(*args,**kwargs)
        self.daemon = True

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
        if name in self._settings_data:
            func_name = 'do_setting_set_'+ name.replace('.','_')
            if hasattr(self,func_name):
                return getattr(self,func_name)(name,value)
            elif self._settings_data[name]['writable'] == 'yes':
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
        self._axis_motor = EmulatorASCIIDeviceAxis()

    def respond(self,**kwargs):
        kwargs['state'] = 'BUSY' if self._axis_motor.moving() else 'IDLE'
        return super(EmulatorASCIIDeviceSingleAxis,self).respond(**kwargs)

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
