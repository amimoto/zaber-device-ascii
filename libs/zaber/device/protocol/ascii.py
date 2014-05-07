import re
import zaber.device.protocol.base as base

class ZaberResponse(dict):
    # Yanked from: 
    # http://goo.gl/7a1WDj

    def __init__(self, *args, **kwargs):
        super(ZaberResponse, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def values(self):
        """ Useful mostly for when accessing settings. This will allow
            users to retrieve a space split list of responses
        """
        return self.message.split(' ')

    def __getattr__(self,k):
        if self.interface:
            return getattr(self.interface,k)
        raise AttributeError(
                "'{}' object has no attribute '{}'".format(type(self).__name__,k)
              )


class ZaberProtocolASCII(base.ZaberProtocol):

    def response_parse(self,response_line,interface):

        message_type = response_line[0]

        parts = response_line.split(' ',2)
        response_type = parts[0][0]
        address = int(parts[0][1:])
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
            return ZaberResponse({
                'message_type': 'reply',
                'address': address,
                'axis': axis,
                'reply_flags': parts[0],
                'warn_flags': parts[1],
                'status': parts[2],
                'message': parts[3],
                'interface': interface
            })

        elif message_type == '#':
            return ZaberResponse({
                'message_type': 'info',
                'address': address,
                'axis': axis,
                'message': message,
                'interface': interface
            })

        elif message_type == '!':
            return ZaberResponse({
                'message_type': 'alert',
                'address': address,
                'axis': axis,
                'message': message,
                'interface': interface
            })

        return

    def request(self,command,*args,**kwargs):

        # What should the device/axis addressing look like?
        command_segments = []
        address = kwargs.get('address',None)
        axis = kwargs.get('axis',None)
        if address != None: command_segments.append(str(address))
        if axis != None: command_segments.append(str(axis))

        # Then we can add the command to be sent to the device
        command_segments.append(command)

        # Construct the request string
        args_str = [str(a) for a in args]
        request_str = "/"+" ".join(command_segments+args_str)+"\r\n"

        # Then send it
        return self._port.write(request_str)

    def response(self,*args,**kwargs):

        # Do we want blocking? By default it's a no
        block = kwargs.pop('block',False)

        # Just in case we want some chain magic
        interface = kwargs.pop('interface',True)

        # Wait for a response. If not blocking, then
        # drop out with a null upon first timeout
        while True:
            l = self._port.readline(*args,**kwargs)
            if not l:
               if block: continue
               return
            r = self.response_parse(l,interface)
            return r

