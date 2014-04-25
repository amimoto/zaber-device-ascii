import re
import datetime

import zaber.device.protocol.ascii as protocol

class InterfaceASCIISetting(str):
    def __new__(cls, key, interface):
        self = super(InterfaceASCIISetting, cls).__new__(cls, None)
        super(InterfaceASCIISetting, self).__setattr__('_interface',interface)
        super(InterfaceASCIISetting, self).__setattr__('_key',key)
        super(InterfaceASCIISetting, self).__setattr__('_value',None)
        return self

    def value_get(self):
        # import pdb; pdb.set_trace()
        response = self._interface.get(self._key)
        raise RuntimeError(
                  "Request for setting value '{}' timed out".format(self._key)
              )
        return response.message

    def __getattr__(self,k):
        return InterfaceASCIISetting(
                    key=self._key+"."+k, 
                    interface=self._interface,
                )

    def __setattr__(self,k,v):
        config_key = self._key+"."+k
        self._interface.set(config_key,v)

    def __str__(self):
        return self.value_get()

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

    _allowed_settings = []

    def __init__(self,*args,**kwargs):

        self._devices = kwargs.pop('devices',None)
        self._address = kwargs.pop('address',None)
        self._axis = kwargs.pop('axis',None)

        self._allowed_commands = kwargs.pop('allowed_commands',self.allowed_commands)
        allowed_commands_regex_str = ( "^(" 
                                    + "|".join(self._allowed_commands) 
                                    + ")(_[_a-z]+)?$" )
        self._allowed_commands_regex = re.compile(allowed_commands_regex_str)

        self._allowed_settings = kwargs.pop('allowed_settings',self.allowed_settings)

        if 'protocol' in kwargs:
            self._protocol = kwargs['protocol']
        else:
            protocol_class = kwargs.pop('protocol_class',protocol.ZaberProtocolASCII)
            self._protocol = protocol_class(*args,**kwargs)

    def request(self, command='', *args, **kwargs):

        blocking_request = not kwargs.pop('nonblock',False)

        # We don't allow blocking requests if the
        # user has not provided a map of the devices
        # on the daisychain
        if blocking_request and  \
           not self._address and \
           not self._axis and \
           not self._devices:
              raise RuntimeError(
                  'Broadcast messages require the daisychain '
                  +'structure to be defined. See the "devices" parameter'
              )


        self._protocol.request(
            command.replace('_', ' '),
            address=self._address,
            axis=self._axis,
            *args
        )

        # If self.request(nonblock=True) the system
        # will not wait for a response before returning
        if blocking_request:
            print "Waiting for response for:", command
            return self._protocol.response(interface=self)
        else: 
            return self

    def response(self,*args,**kwargs):
        return self._protocol.response(interface=self,*args,**kwargs)

    def __getitem__(self,key):
        if self._address == None:
            return type(self)(
                    address=key,
                    protocol=self._protocol,
                    allowed_commands=self._allowed_commands,
                    allowed_settings=self._allowed_settings,
                )
        if self._axis != None:
            raise LookupError("'{}' cannot be used to index below axis".format(key))
        return type(self)(
                address=self._address,
                axis=key,
                protocol=self._protocol,
                allowed_commands=self._allowed_commands,
                allowed_settings=self._allowed_settings,
            )

    def __setattr__(self,k,v):
        if k in self._allowed_settings:
            self.set(k,v)
        else:
            super(InterfaceASCII,self).__setattr__(k,v)

    def __getattr__(self,k):
        if self._allowed_commands_regex.match(k):
            return lambda *args,**kwargs: self.request(k,*args,**kwargs)
        elif k in self._allowed_settings:
            return InterfaceASCIISetting(
                        key=k, 
                        interface=self,
                    )

        raise AttributeError(
                "'{}' object has no attribute '{}'".format(type(self).__name__,k)
              )


class InterfaceASCIIHelpers(InterfaceASCII):
    """ Another layer around the ASCII Interface that provides
        a few convenience functions. Mostly around the ability
        to handle broadcasts nicely
    """
    def autodetect(self,renumber=False):
        """ Checks the daisychain for a list of devices.
            Returns a data structure that can be later fed
            back into system for broadcast message handling

            devices = [
                {
                    address => 1,
                    ...
                },
                {
                    address => 2,
                    ...
                },
            ]

            The returned data structure should be composed of
            simple primitives as it should be storable in
            multiple formats (JSON/pickle/XML/etc) so the 
            users can opt for their favourite serialization scheme
            without gymnastics

        """

        # If this is a new connect, we'll probably want to renumber
        # the daisychain just in case there are multiples
        if renumber:
            self.renumber(nonblock=True)

        # We use the  "/" command by default to look for requests.
        # We just send the request and we'll manually listen for reports
        else:
            self.request(nonblock=True)

        # We fetch all responses until there's 1 second of quiet
        quiet_timeout = 1.0
        quiet_time_start = None
        device_lookup = {}
        while True:
            response = self.response(block=False)
            if response:
                device_lookup.setdefault(response.address,{
                                'address': response.address,
                            })
                quiet_time_start = None
                continue
            if quiet_time_start:
                quiet_time_delta = datetime.datetime.now() - quiet_time_start
                quiet_time_delta = quiet_time_delta.microseconds/1000000.000 \
                                 + quiet_time_delta.seconds
                if quiet_time_delta >= quiet_timeout:
                    break
            else:
                quiet_time_start = datetime.datetime.now()

        # Start asking for device information 
        for address,data in device_lookup.iteritems():
            data['deviceid'] = int(self[address][0].deviceid)
            data['axiscount'] = int(self[address][0].system.axiscount)




