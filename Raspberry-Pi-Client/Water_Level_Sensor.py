#!/usr/bin/env python3

from gpiozero import DistanceSensor, LED
from time import sleep, time

# Water level sensor class
class WaterLevelSensor:
	
	# Water level sensor constructor
    def __init__(self, send_func):
        
        self._send = send_func

        # Ultrasonic sensor to detect the water level on GPIO pins 23 and 24
        self.ultra = DistanceSensor(echo=24, trigger=23)
        # Green LED on GPIO pin 17 to indicate that water was added
        self.led_added = LED(17)
        # Red LED on GPIO pin 27 to indicate that water has evaporated
        self.led_evaporated = LED(27)
        # Yellow LED on GPIO pin 22 to indicate that no significant change in the water level has occurred
        self.led_no_change = LED(22)

        # Height of vase which crop is contained within
        self.VASE_HEIGHT_CM = 19.0
        
        """The amount of water level change which is classified as significant
           to prevent false positive readings when water level is not stable"""
        self.TOLERANCE      = 0.3
           
        self.last_level     = None
        self.last_tx        = 0.0    

    # Helper methods
    # Static method which allows LED to flash a specific colour
    @staticmethod
    def _flash(led):
        led.on(); sleep(0.5); led.off(); sleep(0.5)

    # Loop to gather water level sensor data and flash the respective LED colour
    def loop(self):
        now = time()
        
        # Gather water level sensor data once every second
        if now - self.last_tx < 1.0:       
            return
        self.last_tx = now

		# Distance measured by ultrasonic sensor
        distance_cm = self.ultra.distance * 100.0
        
        # Water level for vase calculated as vase height - distance measured
        level_cm    = max(0.0, self.VASE_HEIGHT_CM - distance_cm)

        # Initial water level sensor reading
        if self.last_level is None:
            msg = f"Water level: {level_cm:.2f} cm. (Initial reading)"
            
        else:
            diff = level_cm - self.last_level
            
            # No significant change in water level when change is <= 0.3 cm
            if abs(diff) <= self.TOLERANCE:
                msg = f"Water level: {level_cm:.2f} cm. (No significant change)"
                self._flash(self.led_no_change)
                
            # Significant water level increase
            elif diff > self.TOLERANCE:
                msg = (f"Water level: {level_cm:.2f} cm. "
                       f"Water added: {diff:.2f} cm.")
                self._flash(self.led_added)
            
            # Significant water level decrease
            else:
                msg = (f"Water level: {level_cm:.2f} cm. "
                       f"Water evaporated: {abs(diff):.2f} cm.")
                self._flash(self.led_evaporated)

        self.last_level = level_cm
        
        # Print water level sensor reading to the terminal
        print(msg)
        
        # Send the water level sensor reading to the server
        self._send(msg)
