import serial
#from serial.tools import list_ports
import struct
import numpy as np
import time
from multiprocessing.managers import BaseManager, NamespaceProxy
from pyquaternion import Quaternion

class SerialPort(serial.Serial):
    """
    SerialPort is a compound class: both a serial.Serial and a publisher class. 
    Each port has a single subscriber connected to it; the class write/read from its serial port 
    and notify its subscriber when serial data is received.
    """
    def __init__(self, port, baudrate=57600, timeout=1.5, write_timeout=0, subscriber=None):
        super().__init__(port, baudrate, timeout=timeout, write_timeout=write_timeout)
        self.listener = subscriber
    # PUBLISHER-RELATED FUNCTIONS: to add listeners (subscribers), 
    # notify them when new data is received and get their data.
    def subscribe(self, subscriber):
        self.listener = subscriber

    def notify(self, data):
        """
        Notify the subscriber (listener) that data has been received
        """
        # If the port has an active subscriber
        if self.listener:
            # If data is a single 'int' then it's the battery level
            if isinstance(data,int): 
                self.listener.compute_battery_level(data)  
            else: 
                self.listener.update(data)
    
    def start_recording(self):
        if self.listener:
            self.listener.is_recording = True

    def stop_recording(self):
        if self.listener:
            self.listener.is_recording = False
    
    def clear_queue(self):
        self.listener.queue = np.empty((1,12), dtype=np.float) 

    def update_plot_data(self):
        return self.listener.plot_data
    
    def update_batt_lvl(self):
        return self.listener.batt_level
    
    #NOTE: This causes an error with the live plotter: do not use
    def get_listener_queue(self):
        return self.listener.queue[1:]
    
    # SERIAL-RELATED FUNCTIONS: read/write from BT port 
    def packets_stream(self, packet_length=27, batt_message_length=2):
        """
        Reads the stream of data transmitted by the serial port
        in packets of fixed lenght and data.
        Returns (acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, mag_x, mag_y, mag_z, quat_0, quat_1, quat_2, quat_3)
        """
        # Empties the buffer from the name of the sensor read by default
        #self.readline()
        # Initializing quantities needed for serial reading
        b = b''
        h = t = count = 0 
        raw_data = []
        batt_lvl_data = []
        while True:
            # Look for the packet header (0xA0)
            while h != 0xa0:
                b = self.read(1)
                if len(b)>0:
                    h = b[0]
                # Battery level is sent among the packets with a different header
                    if h == 0xf0:
                        while t != 0xff and count <= batt_message_length:
                            b = self.read(1)
                            batt_lvl_data.append(b)
                            if len(b)>0:
                                t = b[0]
                            count += 1
                        # Unpack the battery level unsigned int and notify the subscriber
                        batt_lvl = struct.unpack('Bx', b''.join(batt_lvl_data))[0]
                        self.notify(batt_lvl)
                        batt_lvl_data = []
                        t = 0 
            count = 1
            # Once found, read until the packet tail (0xC0)
            # or until the end of the expected packet length
            while h != 0xc0 or count <= packet_length:
                try: 
                    b = self.read(1)
                    raw_data.append(b)
                    if len(b)>0:
                        h = b[0]
                    count += 1
                except Exception as e: 
                    print(f"Couldn't read from {self._port}: {e}")
            # Unpack the bytes received in
            # a proper data structure
            if len(raw_data)==packet_length:
                # Automatically converts raw bytes to a int16 tuple
                data = struct.unpack('hhhhhhhhhhhhhx', b''.join(raw_data))
                self.notify(list(data))
                #print("Packet received")
                #print(f"Data: {data}, {type(data)}")
            
            # Re-initialize the variables to read the next packet
            data = raw_data = []
            count = 0
            b = 0 

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
    """
    Holds a data structure of the packets received by its publisher 
    that is updates at each incoming packet 
    """
    def __init__(self):
        n_samples = 1000
        self.total_lvl = 0.0
        self.g_ideal = np.array([0, 0, 1]) #vettore gravità
        self.batt_level = 0
        self.n_batt_updates = 0
        self.is_recording = False
        self.plot_data = np.zeros((9,n_samples), dtype=np.float)  # Keeping the last 25 values to be plotted
        self.queue = np.empty((1,12), dtype=np.float) 

    def compute_battery_level(self, new_lvl):
        self.total_lvl += new_lvl
        self.n_batt_updates += 1
        self.batt_level = int(self.total_lvl / self.n_batt_updates)
        #print(f"Battery percentage: {self.batt_level}%")

    def update(self, data):
        # Sensitivity values from Laura's code
        acc_sensitivity = (2.0 / 32768.0)  
        gyr_sensitivity = (250.0 / 32768.0)
        mag_sensitivity = (10. * 4800. / 32768.0)

        acc_array = np.array(data[0:3],dtype=np.float) * acc_sensitivity
        gyro_array = np.array(data[3:6], dtype=np.float) * gyr_sensitivity * np.pi/180  # Rad/s conversion
        mag_array = np.array(data[6:9], dtype=np.float) * mag_sensitivity
        quat = np.array(data[9:13], dtype=np.float) / 10000  # These need to be scaled by a factor of 1000
        q = Quaternion(quat)
        inv_q = q.inverse
        acc_fixed_rf = q.rotate(acc_array)  # Rotate acceleration to be aligned with earth RF
        lin_acc_array = np.subtract(acc_fixed_rf, self.g_ideal)  # Subtract gravity
        free_acc_body_rf = inv_q.rotate(lin_acc_array)  # Rotate acceleration to be aligned with body RF again

        # Update only stores packets in the queue when the flag (that can be set false by GUI) allows it  
        if self.is_recording:
            delta_time = time.time() 
            queue_item = np.concatenate((acc_array, gyro_array, mag_array, free_acc_body_rf), axis=None)
            self.queue = np.vstack((self.queue, queue_item))
            print("Update received!")
            print(self.queue.shape)

        # The data is plotted even if the app is not recording data
        # Roll the array to append the data at the end of the array and remove the first entry
        self.plot_data = np.roll(self.plot_data, -1, axis=1)
        self.plot_data[:3, -1] = acc_array
        self.plot_data[3:6, -1] = gyro_array
        self.plot_data[6:9, -1] = mag_array

class SerialPortManager(BaseManager): pass

class SerialProcessProxy(NamespaceProxy):
    # __dunder__ methods of base NamespaceProxy, need to be exposed
    # in addition to the desired methods
    _exposed_ = ('__getattribute__', '__setattr__', '__delattr__','packets_stream', 'start_recording', 'stop_recording', 'clear_queue', 'write_to_serial', 'update_plot_data', 'update_batt_lvl') # 'get_listener_data', 'set_port', 'ports', 'listeners')

    def packets_stream(self):
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('packets_stream')
    def start_recording(self):
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('start_recording')
    def stop_recording(self):
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('stop_recording')
    def clear_queue(self):
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('clear_queue')
    def write_to_serial(self, message):
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('write_to_serial',(message,))
    def update_plot_data(self):
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('update_plot_data')
    def update_batt_lvl(self):
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('update_batt_lvl')

SerialPortManager.register('SerialPort', SerialPort, SerialProcessProxy)






