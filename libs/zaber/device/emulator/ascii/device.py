import threading
import os
import csv
import time

import zaber.device
from zaber.device.emulator.base import *
from zaber.device.emulator.parts import *

from zaber.device.emulator.ascii.axes import *

ascii_device_default_config = {
    'accel': '0',
    'cloop.counts': '0',
    'cloop.mode': '0',
    'cloop.stalltimeout': '0',
    'cloop.steps': '0',
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
    'limit.approach.maxspeed': '0',
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
    'limit.max': '0',
    'limit.min': '0',
    'limit.swapinputs': '0',
    'maxspeed': '0',
    'motion.accelonly': '0',
    'motion.decelonly': '0',
    'peripheralid': '0',
    'pos': '0',
    'resolution': '0',
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

    def settings_load(self,settings_config=None):
        if settings_config == None:
            base_path = os.path.dirname(zaber.device.__file__)
            settings_config = os.path.join(base_path,"data","ascii-settings.csv")
        csv_reader = csv.DictReader(open(settings_config))
        settings_data = ascii_device_default_config.copy() 
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
            func_name = 'do_setting_get_'+ name.replace('.','_')
            if hasattr(self,func_name):
                return getattr(self,func_name)(name,value)
            else:
                return self._settings.get(name,0)
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
            self.address(1)
            command.parameters = [2]
        else:
            self.address(command.parameters[0])
            command.parameters[0] = self.address() + 1
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
        self.respond(
                response_type='#', 
                values='Thank you Mario! But our '\
                        +'princess is in another castle!')
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
            print "RELAY <devid:%s> %s" %(command.address, repr(command))
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

        if int(self.address()) != int(command.address):
            return False

        if command.axis in(0,None,1):
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
