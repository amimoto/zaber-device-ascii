
    def estop(self, ):
        """
        Performs an emergency stop on the axis.
    
        Scope: Axis
        Parameters: 
            
        :returns: 0
        
        """
        return self.blocking_request("estop", )
            
    def get(self, setting):
        """
        Retrieves the current value of the device or axis setting.
    
        Scope: Device and Axis
        Parameters: 
            setting
        :returns: <i>value</i>
        
        """
        return self.blocking_request("get", setting)
            
    def help(self, commands):
        """
        Displays the help information for the system.
    
        Scope: Device
        Parameters: 
            commands
            reply
            command, ...
        :returns: 0
        
        """
        return self.blocking_request("help", commands)
            
    def home(self, ):
        """
        Moves the axis to the home position.
    
        Scope: Axis
        Parameters: 
            
        :returns: 0
        
        """
        return self.blocking_request("home", )
            
    def io_info(self, ai_ao_do_di=None):
        """
        Returns the number of I/O channels the device has.
    
        Scope: Device
        Parameters: 
            ai_ao_do_di=None
        :returns: <i>ports</i>
        
        """
        return self.blocking_request("io info", ai_ao_do_di=None)
            
    def io_get(self, ai_ao_do_di, channel=None):
        """
        Returns the current value of the specified I/O channel type.
    
        Scope: Device
        Parameters: 
            ai_ao_do_di, channel=None
        :returns: <i>value</i>
        
        """
        return self.blocking_request("io get", ai_ao_do_di, channel=None)
            
    def io_set(self, ao, channel, value):
        """
        Sets the specified output channel to value.
    
        Scope: Device
        Parameters: 
            ao, channel, value
            do, channel, value
            do, port, value, value2
        :returns: 0
        
        """
        return self.blocking_request("io set", ao, channel, value)
            
    def l(self, ):
        """
        Repeats the last command.
    
        Scope: Device
        Parameters: 
            
        :returns: 0
        
        """
        return self.blocking_request("l", )
            
    def move(self, abs_rel_vel, value):
        """
        Moves the axis to various positions along its travel.
    
        Scope: Axis
        Parameters: 
            abs_rel_vel, value
        :returns: 0
        
        """
        return self.blocking_request("move", abs_rel_vel, value)
            
    def move(self, min_max):
        """
        Moves the axis to the limits of travel.
    
        Scope: Axis
        Parameters: 
            min_max
        :returns: 0
        
        """
        return self.blocking_request("move", min_max)
            
    def move(self, stored, number):
        """
        Moves the axis to a previously stored position.
    
        Scope: Axis
        Parameters: 
            stored, number
        :returns: 0
        
        """
        return self.blocking_request("move", stored, number)
            
    def renumber(self, value):
        """
        Renumbers all devices in the chain.
    
        Scope: Device
        Parameters: 
            value
        :returns: 0
        
        """
        return self.blocking_request("renumber", value)
            
    def set(self, setting, value):
        """
        Sets the device or axis setting setting to the value.
    
        Scope: Device and Axis
        Parameters: 
            setting, value
        :returns: 0
        
        """
        return self.blocking_request("set", setting, value)
            
    def stop(self, ):
        """
        Decelerates the axis and brings it to a halt.
    
        Scope: Axis
        Parameters: 
            
        :returns: 0
        
        """
        return self.blocking_request("stop", )
            
    def system_reset(self, ):
        """
        Resets the device, as it would appear after power up.
    
        Scope: Device
        Parameters: 
            
        :returns: 0
        
        """
        return self.blocking_request("system reset", )
            
    def system_restore(self, ):
        """
        Restores common device settings to their default values.
    
        Scope: Device
        Parameters: 
            
        :returns: 0
        
        """
        return self.blocking_request("system restore", )
            
    def tools_echo(self, message):
        """
        Echoes the provided message (if any) back to the user.
    
        Scope: Device
        Parameters: 
            message
            
        :returns: 0
        
        """
        return self.blocking_request("tools echo", message)
            
    def tools_findrange(self, ):
        """
        Uses the home and away sensors to set the valid range of the axis.
    
        Scope: Axis
        Parameters: 
            
        :returns: 0
        
        """
        return self.blocking_request("tools findrange", )
            
    def tools_gotolimit(self, limit, dir, action, update):
        """
        Moves the axis to a limit sensor and performs the provided actions.
    
        Scope: Axis
        Parameters: 
            limit, dir, action, update
        :returns: 0
        
        """
        return self.blocking_request("tools gotolimit", limit, dir, action, update)
            
    def tools_parking(self, state_park_unpark):
        """
        Parking allows the device to be turned off and used at a later time without first having to home.
    
        Scope: Device
        Parameters: 
            state_park_unpark
            
        :returns: 0|1
        
        """
        return self.blocking_request("tools parking", state_park_unpark)
            
    def tools_setcomm(self, rs232baud, protocol):
        """
        Sets RS232 baud rate and communication protocol for RS232 and USB.
    
        Scope: Device
        Parameters: 
            rs232baud, protocol
        :returns: 0
        
        """
        return self.blocking_request("tools setcomm", rs232baud, protocol)
            
    def tools_storepos(self, number, position=None):
        """
        Stores a number of positions for easy movement.
    
        Scope: Axis
        Parameters: 
            number, position=None
            
        :returns: 0|<i>position</i>
        
        """
        return self.blocking_request("tools storepos", number, position=None)
            
    def trigger(self, Refer, to, the, documentation, below):
        """
        Configures actions to be performed on the device when a certain condition is met.
    
        Scope: Device
        Parameters: 
            Refer, to, the, documentation, below
        :returns: 0
        
        """
        return self.blocking_request("trigger", Refer, to, the, documentation, below)
            
    def trigger_dist(self, number, axis, displacement):
        """
        Configures a trigger to toggle a digital output line every displacement microsteps.
    
        Scope: Device
        Parameters: 
            number, axis, displacement
            number, enable, count=None
            number, disable
        :returns: 0
        
        """
        return self.blocking_request("trigger dist", number, axis, displacement)
            
    def trigger_time(self, number, period):
        """
        Configures a periodic trigger to toggle a digital output line every period milliseconds.
    
        Scope: Device
        Parameters: 
            number, period
            number, enable, count=None
            number, disable
        :returns: 0
        
        """
        return self.blocking_request("trigger time", number, period)
            
    def warnings(self, clear=None):
        """
        Displays the active device and axis warnings, optionally clearing them if applicable.
    
        Scope: Axis
        Parameters: 
            clear=None
            
        :returns: 0
        
        """
        return self.blocking_request("warnings", clear=None)
            