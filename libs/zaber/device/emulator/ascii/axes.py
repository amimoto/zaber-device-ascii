import threading

class EmulatorASCIIDeviceAxis(threading.Thread):        

    def __init__(self,*args,**kwargs):
        super(EmulatorASCIIDeviceAxis,self).__init__(*args,**kwargs)
        self._settings = kwargs.pop('axis_settings',{})
        self.daemon = True
        self._running = True

        # State of the motor
        self._position_prev = 0
        self._position = 0
        self._position_min = 0
        self._position_max = 305381
        self._velocity = 0
        self._stalled = False

    def motor_velocity(self,*args):
        # FIXME concurrency problem here
        #       read/write to attribs
        if args: self._velocity = args[0]
        return self._velocity

    def motor_position(self):
        # FIXME concurrency problem here
        #       read/write to attribs
        return self._position

    def motor_stop(self):
        self.motor_velocity(0)

    def join(self,timeout=None):
        # FIXME concurrency problem here
        #       read/write to attribs
        self._running = False
        super(EmulatorASCIIDeviceAxis,self).join(timeout)

    def run(self):
        """ Main loop that just runs the "motor"
        """
        time_slice = 0.1
        while self._running == True:
            time.sleep(time_slice)

            position = self._position
            if not self._stalled \
               and position >= self._position_min \
               and position <= self._position_max:
                  delta = int((self._velocity/1.6384)*time_slice)
                  position += delta

            if position < self._position_min: position = self._position_min
            if position > self._position_max: position = self._position_max

            self._position_prev = self._position
            self._position = position

            if self._position != self._position_prev:
                print "MPOS {}".format(self._position)
