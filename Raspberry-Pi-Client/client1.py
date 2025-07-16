#!/usr/bin/env python3

import socket
from time import sleep

# Static IP address of Ubuntu virtual machine
HOST = "192.168.50.20"
# TCP port 6000
PORT = 6000

# Method which utilises TCP to send IoT sensor data to server over port 6000
def send_to_server(line: str) -> None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            
            # Ubuntu virtual machine IP address of "192.168.50.20" and TCP port of 6000
            s.connect((HOST, PORT))
            
            s.sendall(line.encode())
            
            try:
                s.recv(1024)
                
                # Print line to separate IoT sensor readings in terminal
                print("------------------------------------------------------------")
                
            except socket.timeout:
                pass
                
    # Notify user when no connection to server exists, likely due to Ethernet cable not connected or server has not been started
    except Exception as exc:
        print("No connection to server, please connect Ethernet cable and start the server")

# Import water level sensor file
from Water_Level_Sensor import WaterLevelSensor
# Import pest detection sensor file
from Pest_Detection_Sensor import PestDetectionSensor
# Import temperature and humidity sensor file
from Temperature_And_Humidity_Sensor import TemperatureHumiditySensor

def main() -> None:
	# Send respective IoT sensor data to server
    water = WaterLevelSensor(send_to_server)
    pest  = PestDetectionSensor(send_to_server)
    th    = TemperatureHumiditySensor(send_to_server)

    try:
        while True:
			# Run once per main loop iteration
            water.loop()    
            # Also run once per main loop iteration
            th.loop()  
            # Small delay to limit CPU usage     
            sleep(0.05)      
            
    # Terminate client connection
    except KeyboardInterrupt:
		
		# Inform server that client connection has been closed successfully
        send_to_server("Client 1 disconnected")
        # Inform user that client connection has been closed successfully         
        print("\n[Client] Ctrl-C received, client connection closed successfully.")
        
    # Clean exit required by DHT11 temperature and humidity sensor
    finally:
        th.cleanup()      

if __name__ == "__main__":
    main()
