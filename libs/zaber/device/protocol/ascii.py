import zaber.device.protocol.base as base
import re

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
allowed_commands_regex_str = ( "^(" 
                            + "|".join(allowed_commands) 
                            + ")[_a-z]*$" )
allowed_commands_regex = re.compile(allowed_commands_regex_str)


class ZaberResponse(dict):
    # Yanked from: 
    # http://goo.gl/7a1WDj
    def __init__(self, *args, **kwargs):
        super(ZaberResponse, self).__init__(*args, **kwargs)
        self.__dict__ = self

class ZaberASCIITarget(object):
    def __init__(self,device=None,axis=None):
        self._device = device
        self._axis = axis

    def __str__(self):
        elements = []
        if self._device == None: return ''
        if self._axis == None: return self._device
        return self._device + ' ' + self._axis
        

class ZaberASCIIDeviceAxis(object):
    def __init__(self,device,axis):
        self._device = device
        self._axis = axis

    def first(self):
        pass

class ZaberASCIIDeviceMetadata(object):
    pass

class ZaberASCIISettingsSugar(object):
    _base = None
    def __init__(self,base=''):
        self._base = base
    def __str__(self):
        return self._base
    def __setattr__(self,k,v):
        if k == '_base':
            return object.__setattr__(self,k,v)
        pass                        
    def __getattr__(self,k):
        node_str = self._base + "." + k if self._base else k
        return ZaberASCIISettingsSugar(node_str)

class ZaberProtocolASCII(base.ZaberProtocol):

    def response_parse(self,response_line):

        message_type = response_line[0]

        parts = response_line.split(' ',2)
        response_type = parts[0][0]
        device_address = int(parts[0][1:])
        device_axis = int(parts[1])

        message = parts[2].replace('\n','').replace('\r','')

        if message_type == '@':
            parts = message.split(' ',3)
            return ZaberResponse({
                'message_type': 'reply',
                'device_address': device_address,
                'device_axis': device_axis,
                'reply_flags': parts[0],
                'warn_flags': parts[1],
                'device_status': parts[2],
                'message': parts[3]
            })

        elif message_type == '#':
            return ZaberResponse({
                'message_type': 'info',
                'device_address': device_address,
                'device_axis': device_axis,
                'message': message
            })

        elif message_type == '!':
            return ZaberResponse({
                'message_type': 'alert',
                'device_address': device_address,
                'device_axis': device_axis,
                'message': message
            })

        return

    def request(self,command,*args,**kwargs):

        command_segments = command.split('_')

        # First, send the request
        args_str = [str(a) for a in args]
        self._port.write("/"+" ".join(command_segments+args_str)+"\r\n")

    def response(self,*args,**kwargs):

        # Do we want blocking? By default it's a yes
        block = kwargs.pop('block',True)

        # Wait for a response. If not blocking, then
        # drop out with a null upon first timeout
        while True:
            l = self._port.readline()
            if not l:
               if block: continue
               return
            return self.response_parse(l)


    def enumerate(self):
        """ Return a list of devices and axes

            :returns: dict of dicts
        """

        # Sending a simple '/\r\n' just requests all
        # devices to respond with a check-in
        self.request('')

        # FIXME how to determine when responses have completed?
        devices = []
        while True:
            r = self.response(block=False)
            if not r: break
            devices.append(r)

        return devices 


    def __contains__(self,k):
        if allowed_commands_regex.match(k):
            return True
        return False

    def __getattr__(self,k):
        if allowed_commands_regex.match(k):
            return lambda *args, **kwargs: self.request(k,*args,**kwargs)
        raise AttributeError(
                "'{}' object has no attribute '{}'".format(type(self).__name__,k)
              )


