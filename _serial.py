import serial
from serial.tools import list_ports
import asyncio
import struct
import sys


class SerialPort(serial.Serial):
    """
    SerialPort is a compound class: both a serial.Serial and a publisher class. 
    Each port has a single subscriber connected to it; the class write/read from its serial port 
    and notify its subscriber when serial data is received.
    """
    # PUBLISHER-RELATED FUNCTIONS: to add listeners (subscribers) and 
    # notify them when new data is received.
    listener = []
    def subscribe(self, subscriber):
        self.listener.append(subscriber)

    def notify(self):
        for l in self.listener:
            l.update()
    
    # SERIAL-RELATED FUNCTIONS: read/write from BT port 
    def packets_stream(self, packet_length=27):
        """
        Reads the stream of data transmitted by the serial port
        in packets of fixed lenght and data.
        Returns (acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, mag_x, mag_y, mag_z, quat_0, quat_1, quat_2, quat_3)
        """

        # TODO: think of better solution to clean the serial buffer. 
        # It works on first initialization for cleaning the sensor's name string
        self.readline()

        b = b''
        h = 0
        raw_data = []
        while True:
            # Look for the packet header (0xA0)
            while h != 0xa0:
                b = self.read(1)
                if len(b)>0:
                    h = b[0]
            count = 1
            # Once found, read until the packet tail (0xC0)
            # or until the end of the expected packet length
            while h != 0xc0 or count <= packet_length:
                b = self.read(1)
                raw_data.append(b)
                if len(b)>0:
                    h = b[0]
                count += 1
            # Unpack the bytes received in
            # a proper data structure
            if len(raw_data)==packet_length:
                # Automatically converts raw bytes to a int16 tuple
                data = struct.unpack('hhhhhhhhhhhhhx', b''.join(raw_data))
                print("Packet received")
                print(f"Data: {data}, {type(data)}")
            
            # Re-initialize the variables to read the next packet
            data = raw_data = []
            count = 0
            b = 0 


    def read_data(self, end='\n'):
        print(self.in_waiting)
        while self.in_waiting:
            data = self.read_until(end).decode('utf-8', errors='replace')
            return data

    def write_to_serial(self, message):
        """
        Converts the message string passed as argument 
        to a byte array that is sent to the port
        """

        if self.is_open:
            self.write(message.encode('utf8'))
            self.flush()
        else:
            print("Could not write message: the port is closed!")
    
    def check_port(self):
        """
        Initializes the port-related Arduino state machine 
        and returns the name of the port itself
        """
        line=''
        print(self.in_waiting)
        if self.in_waiting:
            print("Incoming data...")
            while('111' not in line):
                c = self.read().decode('utf-8', errors='replace') #leggo un carattere alla volta
                line += c #aggiungo carattere a una stringa
        
        return line.replace('1','')

class SerialSubscriber():
    def __init__(self):
        pass

    def update(self):
        print("Update received!")
        pass
    

class SerialPortManager():
    """
    Adapted from Serial Port Design Pattern. Mantains an array of SerialPort objects. 
    Each SerialPort manages its messages (transmitting / receiving); the
    SerialPortManager implements the interrupt (e.g., when closing the program)
    """

    def __init__(self):
        # Reads list of all the ports detected in a list 
        self.ports_list = [port for port in list_ports.comports()]
        self.ports = {}
    
    def load_ports(self, virtual_ports=None):
        # Initializes the SerialPort objects array
        if virtual_ports is None:
            ports = self.ports_list
        for port in ports[-1:]:
            try:
                if virtual_ports is None and port.device != "/dev/cu.Bluetooth-Incoming-Port":
                    # NOTE: timeout increased to 2 - was 1.5 - to avoid serial exceptions
                    ser = SerialPort(port=port.device, baudrate=57600, timeout=2, write_timeout=0)
                else:
                    print("Connecting to virtual port(s)")
                    ser = SerialPort(port=port, baudrate=57600, timeout=1.5, write_timeout=0)
                if ser.is_open:
                    print(f"Adding subscriber to {ser.name}")
                    s = SerialSubscriber()
                    ser.subscribe(s)
                    print(f"Subscriber added to: {(ser.name)}")
                    self.ports[(ser.name)] = ser
            except: 
                print(f"Could not connect to port: {port}")

        return self.ports

    def interrupt_ports(self):
        pass
    
    def test_process(self):
        # NOTE: debug purposes only
        i = 0 
        while i < 100:
            print(f"Process running: {i}")
            i += 1






