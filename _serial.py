import serial
from serial.tools import list_ports
import asyncio


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
    
    def chunked_stream(self, chunk_size=100):
        """ Read all characters on the serial port and return them. """
        if not self.timeout:
            raise TypeError('Port needs to have a timeout set!')

        read_buffer = b''
        while True:
            try:
                byte_chunk = self.read(chunk_size)
                #print(byte_chunk)
                read_buffer += byte_chunk
                if not len(byte_chunk) == chunk_size:
                    print(f"Decoded: {read_buffer.decode()}")
                    self.notify()
            except Exception as e:
                print(e)
                break

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
        for port in ports:
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






