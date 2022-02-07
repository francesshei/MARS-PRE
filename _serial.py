import serial
from serial.tools import list_ports
import asyncio
import struct
import sys


# TODO check https://stackoverflow.com/questions/21666106/using-serial-port-in-python3-asyncio
class SerialPort(serial.Serial):
    """
    SerialPort is a compound class: both a serial.Serial and a publisher class. 
    Each port has a single subscriber connected to it; the class write/read from its serial port 
    and notify its subscriber when serial data is received.
    """
    listener = []
    def subscribe(self, subscriber):
        self.listener.append(subscriber)

    def notify(self):
        for l in self.listener:
            l.update()
    
    def chunked_stream(self, packet_length=27):
        # TODO: think of better solution to 
        # clean the serial buffer. It works
        # on first initialization for cleaning
        # the sensor's name string
        self.readline()

        b = b''
        h = 0
        raw_data = []
        while True:
            # Look for the packet header
            while h != 0xa0:
                b = self.read(1)
                print(b)
                if len(b)>0:
                    h = b[0]
            count = 1
            # Read until the packet tail (0xC0)
            while h != 0xc0 or count <= packet_length:
                b = self.read(1)
                raw_data.append(b)
                h = b[0]
                count += 1
                #print(len(raw_data))
            if len(raw_data)==packet_length:
                data = struct.unpack('hhhhhhhhhhhhhx', b''.join(raw_data))
                print("Packet received")
                print(f"Data: {data}")
            
            data = raw_data = []
            count = 0
            b = 0 
            """  
                data = self.read()
                if len(data) > 0:
                    raw += data
                    buffer += data
                    #print(buffer[-1])

                    if buffer[0] == 160 and buffer[-1] == 192:
            
            print("Packet received")
            #print(f"Buffered data: {buffer}, len: {len(buffer)}")
            #print(f"Raw data: {raw}, len {len(raw)}")
            acc = [ 
                int.from_bytes(raw[1:3], sys.byteorder),
                int.from_bytes(raw[3:5], sys.byteorder),
                int.from_bytes(raw[5:7], sys.byteorder) 
            ] 
            gyr = [
                int.from_bytes(raw[7:9], sys.byteorder), 
                int.from_bytes(raw[9:11], sys.byteorder),
                int.from_bytes(raw[11:13], sys.byteorder)
            ]
            mag = [
                int.from_bytes(raw[13:15], sys.byteorder), 
                int.from_bytes(raw[15:17], sys.byteorder),
                int.from_bytes(raw[17:19], sys.byteorder)
            ]
            quat = [
                int.from_bytes(raw[19:21], sys.byteorder), 
                int.from_bytes(raw[21:23], sys.byteorder),
                int.from_bytes(raw[23:25], sys.byteorder),
                int.from_bytes(raw[25:27], sys.byteorder)    
            ]
            # Assembling the packet data
            print(f"Acc: {acc}")
            print(f"Gyr: {gyr}")
            print(f"Mag: {mag}")
            print(f"Quat: {quat}")

            buffer = []
            raw = b''
            """


    def read_data(self, end='\n'):
        print(self.in_waiting)
        while self.in_waiting:
            data = self.read_until(end).decode('utf-8', errors='replace')
            return data

    def write_to_serial(self, message):
        # Write bytes to serial port
        if self.is_open:
            self.write(message.encode('utf8'))
        else:
            print("Could not write message: the port is closed!")
    
    def check_port(self):
        line=''
        print(self.in_waiting)
        if self.in_waiting:
            print("Incoming data...")
            while('111' not in line):
                c = self.read().decode('utf-8', errors='replace') #leggo un carattere alla volta
                line += c #aggiungo carattere a una stringa
                #print(line)
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
                    ser = SerialPort(port=port.device, baudrate=57600, timeout=1.5, write_timeout=0)
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






