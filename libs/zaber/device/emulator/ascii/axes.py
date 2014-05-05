import time
import threading

ascii_axis_default_config = {
                'accel': '0',
                'cloop.counts': '0',
                'cloop.mode': '0',
                'cloop.stalltimeout': '0',
                'cloop.steps': '0',
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
                'limit.approach.maxspeed': '153600',
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
                'limit.max': '305381',
                'limit.min': '0',
                'limit.swapinputs': '0',
                'maxspeed': '0',
                'motion.accelonly': '0',
                'motion.decelonly': '0',
                'peripheralid': '0',
                'pos': '0',
                'resolution': '0'
          }

class EmulatorASCIIDeviceAxis(threading.Thread):        

    def __init__(self,*args,**kwargs):
        position = kwargs.pop('pos',0)
        self._axis_number = kwargs.pop('axis_number')

        # Load up some of the settings before we hand over kwargs
        # to thread. (Thread will complain about unexpected parameters
        # otherwise)
        self._settings = kwargs.pop('settings')
        self._axis_settings = ascii_axis_default_config.copy()
        self._axis_settings.update(kwargs.pop('axis_settings'))

        # Resolution of the emulation. Smaller the time slice, more
        # granular... but it also costs more CPU time
        self._time_slice = kwargs.pop('time_slice',0.1)

        super(EmulatorASCIIDeviceAxis,self).__init__(*args,**kwargs)
        self.daemon = True
        self._running = True

        # State of the motor
        self._real_position_prev = int(self._axis_settings['pos'])
        self._real_position = int(self._axis_settings['pos'])
        self._real_position_min = int(self._axis_settings['limit.min'])
        self._real_position_max = int(self._axis_settings['limit.max'])

        self._assumed_position_prev = int(self._axis_settings['pos'])
        self._assumed_position = int(self._axis_settings['pos'])

        self._velocity = 0
        self._moving = False
        self._stalled = False

    def setting_get(self, name):
        func_name = 'do_setting_get_'+ name.replace('.','_')
        if hasattr(self,func_name):
            return int(getattr(self,func_name)(name,value))
        return int(self._axis_settings.get(name,0))

    def setting_set(self, name, value):
        func_name = 'do_setting_set_'+ name.replace('.','_')
        if hasattr(self,func_name):
            return getattr(self,func_name)(name,value)
        self._axis_settings[name] = value
        return self._axis_settings[name]

    def moving(self):
        if self._velocity == 0:
            return False
        return True

    def moving(self):
        """ The 'moving' flag is based upon the assumed position
            of the device
        """
        if not self._velocity: 
            return False
        if self._assumed_position <= self._real_position_min \
            and self._velocity < 0:
                return False
        if self._assumed_position >= self._real_position_max \
            and self._velocity > 0:
                return False
        return True

    def motor_velocity(self,*args):
        if args: self._velocity = args[0]
        return self._velocity

    def motor_real_position(self):
        return self._real_position

    def motor_stop(self):
        self.motor_velocity(0)

    def join(self,timeout=None):
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
        self._axis_settings['pos'] = assumed_position_new
        self._moving = assumed_delta != 0

        # Handle the real movements
        real_position_new = self.move_within_range(self._real_position,assumed_delta)
        self._real_position_prev = self._real_position
        self._real_position = real_position_new

    def run(self):
        """ Main loop that just runs the "motor"
        """
        while self._running == True:
            time.sleep(self._time_slice)

            # Perform the actions required to move the axis
            self.axis_move()

