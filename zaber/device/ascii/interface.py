from __future__ import print_function

import re
import time
import datetime

class DeviceException(Exception): pass
class IndexAtAxis(DeviceException): pass
class RequireDeviceAddress(DeviceException): pass
class ResponseTimeout(DeviceException): pass
class BadCommand(DeviceException): pass

class Setting(object):
    def __init__(self,target,interface,key,*args,**kwargs):
        self.target = target
        self.interface = interface
        self.key = key
        self.value = None

    def get_setting(self,*args,**kwargs):
        if self.value == None: 
            response = self.interface.get(self.key,*args,**kwargs)
            if not response:
                raise ResponseTimeout()
            self.value = response.message
        return self.value

    def __getitem__(self,k):
        value = self.get_setting()
        if k == 0:
            return value
        else:
            return int(value.split(' ')[k-1])

    def __setitem__(self,k,v):
        try:
            i = int(k)
            return self.interface[k].set(self.key,v)
        except ValueError:
            new_key = self.key
            if new_key: new_key += b'.'
            new_key + k
            return type(self)(
              target=self.target,
              interface=self.interface,
              key=new_key
            )

    def __str__(self):
        s = self.get_setting()
        if s == 'BADCOMMAND':
            raise BadCommand()
        return s

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

class SettingAggregate(object):
    target = None
    interface = None
    key = None

    def __init__(self,*args,**kwargs):
        self.target = kwargs.pop('target',Target(kwargs))
        self.interface = kwargs.pop('interface',Target(kwargs))
        self.key = kwargs.pop('key','')

    def __getitem__(self,k):

        if not k:
            raise RequireDeviceAddress()
            return

        return Setting(
            target=self.target.index_into(k),
            interface=self.interface[k],
            key=self.key
        )

    def __setattr__(self,k,v):
        if hasattr(self,k):
            return super(SettingAggregate,self).__setattr__(k,v)
        return

class Target(object):
    def __init__(self, addr=None, axis=None, parent=None, kwargs={}):
        if addr == None and parent:
            addr = parent.addr
        self.addr = addr

        if axis == None and parent:
            axis = parent.axis
        self.axis = axis

        self.parent = parent

    def __nonzero__(self):
        return self.__bool__()
    def __bool__(self):
        return self.addr != None

    def index_into(self,k):
        if self.addr == None:
            return type(self)(addr=int(k),parent=self)
        elif self.axis == None:
            return type(self)(axis=int(k),parent=self)
        else:
            raise IndexAtAxis()

    def __str__(self):
        e = []
        if self.addr != None: e.append(str(self.addr))
        if self.axis != None: e.append(str(self.axis))
        return " ".join(e)

    def __repr__(self):
        return "{}(addr={},axis={})".format(
            type(self).__name__,
            self.addr or 'None',
            self.axis or 'None'
        )

class Request(object):

    def __init__(self,target,cmd,parameters,*args,**kwargs):
        self.target = target
        self.cmd = cmd
        self.parameters = parameters

    def __str__(self):
        e = []
        if self.target: e.append(self.target)
        cmd = self.cmd
        cmd_elements = []
        try:
            cmd_elements = cmd.split(b'_')
        except:
            cmd_elements = cmd.split('_')
        e.extend(cmd_elements)
        if self.parameters: e.extend(self.parameters)

        try:
            request_str = "/"+" ".join([str(i,'utf-8') for i in e])
        except:
            request_str = "/"+" ".join([str(i) for i in e])
        return request_str

    def __repr__(self):
        return "{}(target={},cmd={},parameters={})".format(
            type(self).__name__,
            repr(self.target),
            repr(self.cmd),
            repr(self.parameters)
          )

class Response(dict):
    _interface = None

    def __init__(self, response_line, *args, **kwargs):
        parsed = self.parse(response_line)
        parsed['raw'] = response_line
        super(Response, self).__init__(parsed,*args, **kwargs)
        self._interface = kwargs.get('interface')
        self.__dict__ = self

    def parse(self, response_line):

        line_vals = [hex(ord(i)) for i in response_line]
        message_type = response_line[0]

        parts = response_line.split(' ',2)
        response_type = parts[0][0]
        addr = int(parts[0][1:])
        axis = int(parts[1])

        message = parts[2].replace('\n','').replace('\r','')

        # Check for checksum
        m = re.match('^(.*):(\w\w)$',message)
        checksum = None
        if m:
            message = m.group(1)
            checksum = m.group(2)

        if message_type == '@':
            parts = message.split(' ',3)
            return {
                'type': 'reply',
                'addr': addr,
                'axis': axis,
                'reply_flags': parts[0],
                'status': parts[1],
                'warn_flags': parts[2],
                'message': parts[3],
            }

        elif message_type == '#':
            return {
                'type': 'info',
                'addr': addr,
                'axis': axis,
                'message': message,
            }

        elif message_type == '!':
            return {
                'type': 'alert',
                'addr': addr,
                'axis': axis,
                'message': message,
            }

        return

    def interface(self,interface=None):
        if interface:
            self._interface = interface
        return self._interface

    def values(self):
        """ Useful mostly for when accessing settings. This will allow
            users to retrieve a space split list of responses
        """
        return self.message.split(' ')

    def match(self,target):
        """ Return true if the target matches this response

            Target(None,None): Matches all
            Target(0,None): Match everything

            Target(1,None): Match all device 1
              @01 X = okay

            Target(1,1): Match all device 1 axis 1
              @01 1 = okay
              @01 0 = okay
              @02 0 = no
              @02 1 = no


        """
        if target.addr in [None,0] or self.addr == target.addr:
            if target.axis in [None,0] or self.axis in [target.axis,0]:
                return True
        return False

    def __getattr__(self,k):
        if self._interface:
            return getattr(self._interface,k)
        elif k in self:
            return self[k]
        raise AttributeError(
                "'{}' object has no attribute '{}'".format(type(self).__name__,k)
              )

class Metadata(object):
    timeout = None

    def __init__(self,args,kwargs):
        self.port = kwargs.pop('port',None)
        self.debug = kwargs.pop('debug',False)
        if not self.port:
            from zaber.device.ascii.port.serial import PortSerial
            self.port = PortSerial(*args,**kwargs)
        self.timeout = kwargs.pop('timeout',1)

    def filter (self, target):
        pass

    def request(self,request):
        request_str = str(request)
        if self.debug: print("TODEV:", request_str)
        self.port.writeline(request_str)

    def response_next(self,*args,**kwargs):
        """ Get the next response/alert/info that
            comes from the port. 
        """

        # Make sure that the newlines have been removed from the
        # read line (no reason, just because). More important, ensure
        # that the 0x00 char has been removed from the received line
        # as it causes problems for the parser (not sure why 
        # it is receiving the 0x00s either)
        response_line = self.port.readline(*args,**kwargs).strip()

        # Python2/3 hack
        try:
            response_line = response_line.translate(None,chr(0))
        except TypeError:
            response_line = response_line.translate({b'\0':None})
            

        if self.debug and response_line:
            print("FRMDEV:", response_line)
        if response_line:
            try:
                return Response(response_line)
            except:
                # FIXME: Currently ignores broken messages instead of
                #        reporting the error
                pass 
        return

    def response(self,target=None,*args,**kwargs):
        """ Receive a response from the port. 
        
            If no target is specified, this simply returns 
            the next response.

            If a target is specified, it will query until
            a match is found.
        """

        time_start = datetime.datetime.now()
        while 1:
            resp = self.response_next(*args,**kwargs)
            if not resp: 
                time_delta = datetime.datetime.now() - time_start
                time_delta_seconds = time_delta.seconds + time_delta.microseconds/1000000.000 
                if time_delta_seconds >= self.timeout:
                    break
                time.sleep(0.1)
                continue
            if resp.type != 'reply': continue
            if target and not resp.match(target): continue
            return resp

        return

    def query(self,request):
        target = request.target
        self.request(request)
        return self.response()

    def request_allowed(self,request):
        if request.target.addr:
            return True
        return False

class SettingsInterface(object):
    target = None
    interface = None
    key = None

    def __init__(self,*args,**kwargs):

        self.target = kwargs.pop('target')
        self.interface = kwargs.pop('interface')

        self.key = kwargs.pop('key','')

    def get_setting(self,*args,**kwargs):

        if not self.target.addr:
            return SettingAggregate(
                target=self.target,
                interface=self.interface,
                key=self.key
            )

        else:
            return Setting(
                target=self.target,
                interface=self.interface,
                key=self.key
            )

        return response

    def set_setting(self,*args,**kwargs):
        return self.interface.set(self.key, *args, **kwargs)

    def __call__(self,*args,**kwargs):
        return self.get_setting(*args,**kwargs)

    def __getitem__(self,k):
        try:
            i = int(k)
            s = self.get_setting()
            return s[i]
        except ValueError:
            new_key = self.key
            if new_key: new_key += "."
            new_key += k
            return  type(self)(
                          target=self.target,
                          interface=self.interface,
                          key=new_key
                        ).get_setting()

    def __setitem__(self,k,v):
        try:
            i = int(k)
            return self.interface[k].set(self.key,v)
        except ValueError:
            new_key = self.key
            if new_key: new_key += "."
            new_key += k
            return self.interface.set(new_key,v)

    def __getattr__(self,k):
        new_key = self.key
        if new_key: new_key += "."
        new_key += k
        return type(self)(
                  target=self.target,
                  interface=self.interface,
                  key=new_key
                )

    def __setattr__(self,k,v):
        # Hack to ensure that settings don't get caught in this test
        if k in dir(self):
            return super(SettingsInterface,self).__setattr__(k,v)

        # We're trying to set a setting.
        return self.__setitem__(k,v)

    def __str__(self):
        if not self:
            return type(self).__name__
        if self.key:
            return str(self.get_setting())
        return super(SettingsInterface,self).__str__()

    def __repr__(self):
        if not self:
            return type(self).__name__
        return super(SettingsInterface,self).__repr__()


class DeviceCustomMetadata(object):
    def __init__(self,target,custom_metadata):
        self._target = target
        self.custom_metadata = custom_metadata

    def __getitem__(self,k):
        target = self._target
        metadata = self.custom_metadata
        if target.addr:
            metadata = metadata[target.addr]
            if target.axis:
                return metadata['peripherals'][target.axis][k]
        
        return metadata[k]

    def __getattr__(self,k):
        return self.__getitem__(k)

class DeviceInterface(object):

    target = None
    metadata = None
    s = None
    m = None

    def __init__(self,*args,**kwargs):
        self.debug = kwargs.get('debug',False)
        self.target = kwargs.get('target') or Target(kwargs=kwargs)
        self.metadata = kwargs.get('metadata') or Metadata(args,kwargs)
        self._custom_metadata = kwargs.get('custom_metadata') or {}
        self.s = SettingsInterface(
                      target=self.target,
                      interface=self,
                  )
        self.m = DeviceCustomMetadata(
                      target=self.target,
                      custom_metadata=self._custom_metadata
                  )

    def __getitem__(self,k):
        new_target = self.target.index_into(k)
        new_interface = type(self)(
                            target=new_target,
                            metadata=self.metadata,
                            custom_metadata=self._custom_metadata
                        )
        return new_interface

    def __getattr__(self,k):
        return lambda *a,**kw: self.query(k,*a,**kw)

    def __setattr__(self,k,v):
        if hasattr(self,k):
            return super(DeviceInterface,self).__setattr__(k,v)

    def __str__(self):
        if not self:
            return type(self).__name__
        return super(DeviceInterface,self).__str__()

    def __repr__(self):
        if not self:
            return type(self).__name__
        return super(DeviceInterface,self).__repr__()

    def request(self,cmd=b'',*args,**kwargs):
        req = Request(self.target,cmd,args,**kwargs)
        return self.metadata.request(req)

    def response(self,target=None):
        if target == None:
            target = self.target
        resp = self.metadata.response(target)
        if not resp: return
        resp.interface(self)
        return resp

    def query(self,cmd='',*args,**kwargs):
        req = Request(self.target,cmd,args,**kwargs)
        if not self.metadata.request_allowed(req):
            raise RequireDeviceAddress()
        self.metadata.request(req)
        resp = self.metadata.response(self.target)
        if not resp: 
            raise ResponseTimeout()
        resp.interface(self)
        return resp

    def wait(self):
        while 1:
            result = self.query()
            if result.status == 'IDLE':
                break
            time.sleep(0.1)
        return result


class Interface(DeviceInterface):

    def __init__(self,*args,**kwargs):
        super(Interface,self).__init__(*args,**kwargs)

    def autodetect(self,renumber=False):
        pass


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
            self.request('renumber')

        # We use the  "/" command by default to look for requests.
        # We just send the request and we'll manually listen for reports
        else:
            self.request()

        # We fetch all responses until there's 0.5 seconds of quiet
        quiet_timeout = 0.5
        quiet_time_start = None
        device_lookup = {}
        while True:
            response = self.response()
            if response:
                device_lookup.setdefault(response.addr,{
                                'address': response.addr,
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
        for addr,data in device_lookup.items():
            data['deviceid']  = int(self[addr][0].s.deviceid())
            data['axiscount'] = int(self[addr][0].s.system.axiscount())

        return device_lookup





