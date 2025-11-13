import serial
import time
import regex as re

ser = serial.Serial('COM3', 9600, timeout = 1)
time.sleep(2)  # wait for Arduino to initialize

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode().strip() # Read a line and decode

            #Use regex to find all numbers in the received line
            numbers = re.findall(pattern=r"[-+]?\d*\.\d+|[-+]?\d+", string=line)

            #print the extracted sensor values
            print(f"Extracted values:{numbers}")
except KeyboardInterrupt:
    print("Stopped by user")

Finally:(
    ser.close()) #Close the serial connection when done