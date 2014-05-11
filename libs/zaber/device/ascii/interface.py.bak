import re
import datetime

import zaber.device.protocol.ascii as protocol

class InterfaceASCIISetting(str):
    def __new__(cls, key, interface,address=None,axis=None):
        self = super(InterfaceASCIISetting, cls).__new__(cls, None)
        super(InterfaceASCIISetting, self).__setattr__('_interface',interface)
        super(InterfaceASCIISetting, self).__setattr__('_key',key)
        super(InterfaceASCIISetting, self).__setattr__('_address',address)
        super(InterfaceASCIISetting, self).__setattr__('_axis',axis)
        super(InterfaceASCIISetting, self).__setattr__('_value',None)
        return self

    def value_get(self,**kwargs):
        """ This function is a bit more complicated than desireable
            to accomodate broadcast requests.
        """
        if 'address' not in kwargs and self._address != None: 
            kwargs['address'] = self._address

        if 'axis' not in kwargs and self._axis != None: 
            kwargs['axis'] = self._axis

        response = self._interface.get(self._key,**kwargs)
        if not response:
            raise RuntimeError(
                      "Request for setting value '{}' timed out".format(self._key)
                  )

        address = kwargs.get('address') or self._interface._address
        if address:
            return response[address].message
        return response

    def __getattr__(self,k):
        return InterfaceASCIISetting(
                    key=self._key+"."+k, 
                    interface=self._interface,
                )

    def __setattr__(self,k,v):
        config_key = self._key+"."+k
        self._interface.set(config_key,v)

    def __call__(self,value=None,**kwargs):
        if value == None:
            return self.value_get(**kwargs)
        return self._interface.set(self._key,value,**kwargs)

    def __str__(self):
        return str(self.value_get())

    def __repr__(self):
        return self.__str__()

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

class InterfaceASCIISettingAggregate(dict):
    def __init__(self,*args,**kwargs):
        self._interface = kwargs.pop('interface')
        self._address = kwargs.pop('address')
        self._axis = kwargs.pop('axis')
        self._key = kwargs.pop('key')

        devices = self._interface.devices()

        if self._address:
            # FIXME: What for devices without an axis? (A-JOY?)
            device = devices[self._address]
            for i in range(device.get('axiscount',0)):
                axis = i + 1
                axis_setting = InterfaceASCIISetting(
                                    key=self._key,
                                    address=self._address,
                                    axis=axis,
                                    interface=self._interface,
                                )

                self.setdefault(axis,axis_setting)


        else:
            # FIXME: What for devices without an axis? (A-JOY?)
            for address,device in devices.iteritems():
                for i in range(device.get('axiscount',0)):
                    axis = i + 1
                    axis_setting = InterfaceASCIISetting(
                                        key=self._key,
                                        address=address,
                                        axis=axis,
                                        interface=self._interface,
                                    )

                    self.setdefault(address,{})\
                        .setdefault(axis,axis_setting)

    def __getitem__(self,k):

        if self._address != None:
            if self._axis:
                raise RuntimeError("Can't index below device!")
            else:
                return InterfaceASCIISetting(
                            key=self._key,
                            address=self._address,
                            axis=int(k),
                            interface=self._interface,
                        )
        else:
            return InterfaceASCIISettingAggregate(
                        key=self._key,
                        address=int(k),
                        axis=self._axis,
                        interface=self._interface,
                    )

        return {}


class ZaberResponseAggregate(dict):
    """
      For Broadcast responses.
    """
    def __init__(self,*args,**kwargs):
        self._interface = kwargs.get('interface',None)

    def busy(self):
        """ Returns true when the targetted devices/axis return
            the busy state
        """
        for address,resp in self.iteritems():
            if not resp.busy(address=address,axis=0):
                return False
        return True

    def busy_wait(self):
        """ Wait until the device becomes idle
        """
        while self.busy():
            pass
        return self

    def w(self):
        """ Alias for obj.busy_wait 
        """
        return self.busy_wait()

    def __getattr__(self,k):
        """ Used to allow passthrough of requests to the interface
        """
        return self._interface.__getattr__(k)


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
        self._timeout = kwargs.pop('timeout',1)

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

    def devices(self):
        return self._devices

    def request(self, command='', *args, **kwargs):

        blocking_request = not kwargs.pop('nonblock',False)

        devices = kwargs.get('devices',self._devices)
        address = kwargs.get('address',self._address)
        axis = kwargs.get('axis',self._axis)

        # We don't allow blocking requests if the
        # user has not provided a map of the devices
        # on the daisychain
        if blocking_request and  \
           not address and \
           not axis and \
           not devices:
              raise RuntimeError(
                  'Broadcast messages require the daisychain '
                  +'structure to be defined. See the "devices" parameter'
              )

        self._protocol.request(
            command.replace('_', ' '),
            address=address,
            axis=axis,
            *args
        )

        # If self.request(nonblock=True) the system
        # will not wait for a response before returning
        if blocking_request:
            return self.response_aggregate(
                                      interface=self,
                                      address=address,
                                      axis=axis,
                                      devices=devices,
                                      timeout=self._timeout
                                  )
        else: 
            return self

    def response(self,*args,**kwargs):
        kwargs['timeout'] = self._timeout
        r = self._protocol.response(interface=self,*args,**kwargs)
        return r

    def response_aggregate(self,*args,**kwargs):
        """
        Instead of simply capturing the next response and simply
        returning it, aggregate using the scope rules defined
        by device and axis.

        For this method to work properly, 'devices' must be defined
        in the object.
        """

        address = kwargs.pop('address')
        axis = kwargs.pop('axis')
        devices = kwargs.pop('devices',self._devices)

        # We don't allow blocking requests if the
        # user has not provided a map of the devices
        # on the daisychain
        if not devices:
            raise RuntimeError(
                'Broadcast messages require the daisychain '
                +'structure to be defined. See the "devices" parameter'
            )

        # Figure out which of the device list entries we are 
        # waiting for
        if not address:
            waiting_devices = set(devices.keys())
        else:
            waiting_devices = set([address])

        # FIXME: What to do with the unwanted responses?
        responses = ZaberResponseAggregate(interface=self)
        while waiting_devices:
            r = self.response()
            r_address = r.address
            responses[r_address] = r
            waiting_devices -= set([r.address])

        return responses

    def __getitem__(self,key):
        if self._address == None:
            return type(self)(
                    address=int(key),
                    protocol=self._protocol,
                    devices=self._devices,
                    allowed_commands=self._allowed_commands,
                    allowed_settings=self._allowed_settings,
                )
        if self._axis != None:
            raise LookupError("'{}' cannot be used to index below axis".format(key))
        return type(self)(
                address=self._address,
                axis=int(key),
                protocol=self._protocol,
                devices=self._devices,
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

            # If the device and axis have been set, we have directly tried to
            # access an axis setting so we'll allow that.
            if self._address:
                return InterfaceASCIISetting(
                            key=k, 
                            interface=self,
                        )
            else:
                return InterfaceASCIISettingAggregate(
                            key=k,
                            address=self._address,
                            axis=self._axis,
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

    def busy(self,*args,**kwargs):
        kwargs.pop('axis',None)
        resp = self.request(*args,**kwargs)
        for r in resp.values():
            if r.warn_flags == 'BUSY':
                return True
        return False


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
            data['deviceid'] = int(self[address][0].deviceid(devices=device_lookup))
            data['axiscount'] = int(self[address][0].system.axiscount(devices=device_lookup))

        return device_lookup



