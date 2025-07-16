#!/usr/bin/env python3

from time import time, sleep
import board, adafruit_dht

# Temperature and humidity sensor class
class TemperatureHumiditySensor:
	
	# Temperature and humidity sensor constructor
    def __init__(self, send_func):
        self._send = send_func

		# DHT11 temperature and humidity sensor on GPIO pin 4
        self.dht = adafruit_dht.DHT11(board.D4)
        self.INTERVAL = 2.0
        self.last_tx  = 0.0

        self.last_temp = None
        self.last_hum  = None
	
	# Loop to gather temperature and humidity sensor data
    def loop(self):
        now = time()
        
        if now - self.last_tx < self.INTERVAL:
            return
        self.last_tx = now

        try:
            temp_c = self.dht.temperature
            hum    = self.dht.humidity
            
            # Indicate when no sensor readings are being received
            if temp_c is None or hum is None:
                raise RuntimeError("Sensor error")

            if self.last_temp is None:
                delta_t = "—"; delta_h = "—"
                
            # Calculate the changes in temperature and humidity IoT sensor data readings
            else:
                delta_t = f"{temp_c - self.last_temp:+.1f}°C"
                delta_h = f"{hum    - self.last_hum:+.1f}%"

			# Print IoT sensor data readings and respective changes to user
            line = (f"Temperature: {temp_c:4.1f} °C (Δ {delta_t})   "
                    f"Humidity: {hum:4.1f}% (Δ {delta_h})")
            print(line)
            
            # Send the IoT sensor data readings and respective changes to server
            self._send(line)

            self.last_temp = temp_c
            self.last_hum  = hum

        except RuntimeError as e:
            # Indicate when DHT11 timing error occurs
            print("DHT read error:", e.args[0])

    # DHT11 temperature and humidity sensor requires a clean exit
    def cleanup(self):
        self.dht.exit()
