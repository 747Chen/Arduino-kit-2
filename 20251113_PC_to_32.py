import serial
import time
from datetime import datetime
import regex as re

ser = serial.Serial('COM3', 9600, timeout = 1)
time.sleep(2)  # wait for Arduino to initialize

try:
    while True:
        current_time = datetime.now()

        if current_time.second % 30 < 15:
            command = 'H'
        else:
            command = 'L'

        ser.write(command.encode())
        print(f"Send command: {command} at {current_time.strftime('%H:%M:%S')}")

        time.sleep(1)

except KeyboardInterrupt:
    print("Stopped by user")

finally:(
    ser.close())