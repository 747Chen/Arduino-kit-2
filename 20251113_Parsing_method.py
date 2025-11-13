import serial
import time

# Set up the serial port
ser = serial.Serial('COM7', 9600, timeout=1)
time.sleep(2)  # Wait for Arduino to initialize

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode().strip()   # e.g. "148;179;"
            
            # Remove trailing semicolon and split
            parts = line.split(';')                  # ["148", "179", ""]
            parts = [p for p in parts if p != ""]    # remove empty elements

            # Convert to integers
            numbers = list(map(int, parts))          # [148, 179]

            print(f"Extracted values: {numbers}")

except KeyboardInterrupt:
    ser.close()
