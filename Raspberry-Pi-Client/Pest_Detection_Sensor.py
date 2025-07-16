#!/usr/bin/env python3

from gpiozero import DigitalInputDevice
from time import sleep

# Pest detection sensor class
class PestDetectionSensor:
    def __init__(self, send_func):
        self._send = send_func
        
        # Initialise total pest count to zero
        self.pest_count = 0

		# PIR motion sensor GPIO pin number 5
        PIR_PIN     = 5
        
        # Grant PIR motion sensor 5 seconds to stabilise
        SETTLE_TIME = 5
        print(f"Please wait {SETTLE_TIME}s for the water level sensor to stabilise …")
        sleep(SETTLE_TIME)

        self.pir = DigitalInputDevice(PIR_PIN, pull_up=False)
        
        # When motion is detected my PIR motion sensor
        self.pir.when_activated = self._handle_motion
     

    # Method to handle when motion of pest is detected
    def _handle_motion(self):
		
		# Increase the total pest count by 1
        self.pest_count += 1
        print("Pest Detected")
        print(f"Total Pests Detected: {self.pest_count}")

		# Send the pest detection indication to the server
        self._send("Pest Detected")
        
        # Send the total number of pests detected to the server
        self._send(f"Total Pests Detected: {self.pest_count}")
