import re

import zaber.device.port.serial as port
import zaber.device.protocol.ascii as protocol

TYPE_ROOT = 'root'
TYPE_DEVICE = 'device'
TYPE_AXIS = 'axis'
TYPE_COMMAND = 'command'
TYPE_SETTING = 'setting'

class InterfaceASCIISetting(str):
    def __new__(cls, key, protocol, device=None, axis=None):
        self = super(InterfaceASCIISetting, cls).__new__(cls, None)
        super(InterfaceASCIISetting, self).__setattr__('_device',device)
        super(InterfaceASCIISetting, self).__setattr__('_axis',axis)
        super(InterfaceASCIISetting, self).__setattr__('_protocol',protocol)
        super(InterfaceASCIISetting, self).__setattr__('_key',key)
        super(InterfaceASCIISetting, self).__setattr__('_value',None)
        return self

    def __getattr__(self,k):
        return InterfaceASCIISetting(
                    key=self._key+"."+k, 
                    protocol=self._protocol,
                    device=self._device,
                    axis=self._axis
                )

    def __setattr__(self,k,v):
        print "trying to set property:", k, "to", v

    def __str__(self):
        if self._value == None:
            super(InterfaceASCIISetting, self).__setattr__('_value','1234')
            return self._value
        else:
            return self._value

    def __add__(self, other):
        return str(self) + str(other)

    def __gt__(self, other):
        return str(self) > str(other)

    def __lt__(self, other):
        return str(self) < str(other)

    def __ge__(self, other):
        return str(self) >= str(other)

    def __le__(self, other):
        return str(self) <= str(other)

    def __int__(self):
        return int(str(self))

    def __long__(self):
        return long(str(self))

    def __float__(self):
        return float(str(self))

    def __complex__(self):
        return complex(str(self))

    def __oct__(self):
        return oct(str(self))

    def __hex__(self):
        return hex(str(self))

    def __index__(self):
        return int(str(self))


class InterfaceASCII(object):

    allowed_commands = [
                         'estop',
                         'get',
                         'help',
                         'home',
                         'io',
                         'io_info',
                         'io_set',
                         'l',
                         'move',
                         'renumber',
                         'set',
                         'stream',
                         'stop',
                         'system_reset',
                         'system_restore',
                         'tools_echo',
                         'tools_findrange',
                         'tools_gotolimit',
                         'tools_parking',
                         'tools_setcomm',
                         'tools_storepos',
                         'trigger',
                         'trigger_dist',
                         'trigger_time',
                         'warnings',
                      ]

    allowed_settings = [
                            'knob',
                            'maxspeed',
                            'system',
                            'driver',
                            'accel',
                            'encoder',
                            'motion',
                            'pos',
                            'peripheralid',
                            'comm',
                            'deviceid',
                            'version',
                            'cloop',
                            'limit',
                            'resolution'
                        ]

    def __init__(self,*args,**kwargs):

        self._device = kwargs.pop('device',None)
        self._axis = kwargs.pop('axis',None)
        self._type = kwargs.pop('type',TYPE_ROOT)

        self._allowed_commands = kwargs.pop('allowed_commands',self.allowed_commands)
        allowed_commands_regex_str = ( "^(" 
                                    + "|".join(self._allowed_commands) 
                                    + ")(_[_a-z]+)?$" )
        self._allowed_commands_regex = re.compile(allowed_commands_regex_str)

        self._allowed_settings = kwargs.pop('allowed_settings',self.allowed_settings)

        if 'protocol' in kwargs:
            self._protocol = kwargs['protocol']
        else:
            port_class = kwargs.setdefault('port_class',port.ZaberPortSerial)
            protocol_class = kwargs.pop('protocol_class',protocol.ZaberProtocolASCII)
            self._protocol = protocol_class(*args,**kwargs)

    def __getitem__(self,key):
        if self._device == None:
            return type(self)(
                    device=key,
                    protocol=self._protocol,
                    type=TYPE_DEVICE,
                    allowed_commands=self._allowed_commands,
                    allowed_settings=self._allowed_settings,
                )
        if self._axis != None:
            raise LookupError("'{}' cannot be used to index below axis".format(key))
        return type(self)(
                device=key,
                protocol=self._protocol,
                type=TYPE_AXIS,
                allowed_commands=self._allowed_commands,
                allowed_settings=self._allowed_settings,
            )

    def __getattr__(self,k):
        if self._type == TYPE_SETTING:
            pass
        elif self._allowed_commands_regex.match(k):
            def magic_request(command,*args,**kwargs):
                return self._protocol.request(
                    command.replace('_', ' '),
                    device=self._device,
                    axis=self._axis
                )
            return lambda *args,**kwargs: magic_request(k,*args,**kwargs)
        elif k in self._allowed_settings:
            return InterfaceASCIISetting(
                        key=k, 
                        protocol=self._protocol,
                        device=self._device,
                        axis=self._axis
                    )

        raise AttributeError(
                "'{}' object has no attribute '{}'".format(type(self).__name__,k)
              )






