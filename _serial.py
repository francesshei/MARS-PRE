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
        self.listener.update()

    def start_stream(self):
        # NOTE: this function has to run within a thread 
        # in order to avoid program freezing
        print("Starting the stream reading...")
        while True:
            #print(self.in_waiting)
            if self.in_waiting:
                decoded_bytes = self.read(100000)
                #print(decoded_bytes)

    """ 
            if self.in_waiting > 0:
                try:
                    print("Reading something")
                    decoded_bytes = self.read(100000)
                    print(decoded_bytes)
                    self.notify()
                except:
                    print("Keyboard Interrupt")
                    break
    """

    def read_data(self, end='\n'):
        print(self.in_waiting)
        while self.in_waiting:
            data = self.read_until(end).decode('utf-8', errors='replace')
            return data

    def write_to_serial(self, message):
        # Write bytes to serial port
        if self.is_open:
            self.write(message.encode())
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
        return line.replace('1','')
                #char_counter -= 1
                #if (char_counter == 0): #se raggiungo 100 caratteri senza trovare '111' esco
                #    break

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
    
    def load_ports(self, ports=None):
        # Initializes the SerialPort objects array
        if ports is None:
            ports = self.ports_list
        for port in ports:
            try: 
                if ports is None:
                    ser = SerialPort(port=port.name, baudrate=57600, timeout=1.5, write_timeout=0)
                else:
                    print("Connecting to virtual port(s)")
                    ser = SerialPort(port=port)
                if ser.is_open:
                    print(f"Adding subscriber to {ser.name}")
                    s = SerialSubscriber()
                    ser.subscribe(s)
                    print(f"Subscriber added to: {(ser.name)}")
                    self.ports[(ser.name)] = ser
            except: 
               print(f"Couldn't connect to the port: {ser.name}")
        
        return self.ports

    def interrupt_ports(self):
        pass






