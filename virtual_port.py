import os, pty 
import time
import serial

class VirtualSerialWriter(serial.Serial):
    """
    Virtual serial port, for debug purposes.
    Writes a continuous stream of bytes with intervals
    """
    def __init__(self):
        master, slave = pty.openpty()
        port_name = os.ttyname(slave)
        print(f"Port open on {port_name}")
        self.ser = serial.Serial(port_name,baudrate=57600, timeout=1.5, write_timeout=0)

    def write_stream(self, interval=2):
        while True:
            print("Message sent")
            self.ser.write("Test".encode())
            time.sleep(interval)


if __name__=="__main__":
    v = VirtualSerialWriter()
    v.write_stream()