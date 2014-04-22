import time
import threading

class EmulatorASCIIDeviceAxis(threading.Thread):        

    def __init__(self,*args,**kwargs):
        super(EmulatorASCIIDeviceAxis,self).__init__(*args,**kwargs)
        self._settings = kwargs.pop('axis_settings',{})
        self.daemon = True
        self._running = True

        # State of the motor
        self._real_position_prev = 0
        self._real_position = 0
        self._real_position_min = 0
        self._real_position_max = 305381

        self._assumed_position = 0

        self._velocity = 0
        self._stalled = False

        # Resolution of the emulation. Smaller the time slice, more
        # granular... but it also costs more CPU time
        self._time_slice = kwargs.pop('time_slice',0.1)

    def motor_velocity(self,*args):
        # FIXME concurrency problem here
        #       read/write to attribs
        if args: self._velocity = args[0]
        return self._velocity

    def motor_real_position(self):
        # FIXME concurrency problem here
        #       read/write to attribs
        return self._real_position

    def motor_stop(self):
        self.motor_velocity(0)

    def join(self,timeout=None):
        # FIXME concurrency problem here
        #       read/write to attribs
        self._running = False
        super(EmulatorASCIIDeviceAxis,self).join(timeout)

    def move_within_range(self,position,delta):
        """ Given a start position and a delta,
            returns how far the system would allow
            it to go
        """
        position_new = position + delta

        if position_new < self._real_position_min: 
            position_new = self._real_position_min
        if position_new > self._real_position_max: 
            position_new = self._real_position_max

        return position_new

    def axis_move(self):
        """ This initial code simply performs the current
            move requirements without considering the position
            of the physical stage. (This is a base class that
            emulates an axis without an encoder)
        """
        delta = int((self._velocity/1.6384)*self._time_slice)

        # We handle the physical movements separately than the
        # virtual movements

        # Handle the virtual movements
        assumed_position_new = self.move_within_range(self._assumed_position,delta)
        assumed_delta = assumed_position_new - self._assumed_position
        self._assumed_position_prev = self._assumed_position
        self._assumed_position = assumed_position_new

        # Handle the real movements
        real_position_new = self.move_within_range(self._real_position,assumed_delta)
        self._real_position_prev = self._real_position
        self._real_position = real_position_new

        if self._real_position != self._real_position_prev:
            print "MPOS {}".format(self._real_position)

    def run(self):
        """ Main loop that just runs the "motor"
        """
        while self._running == True:
            time.sleep(self._time_slice)

            # Perform the actions required to move the axis
            self.axis_move()

