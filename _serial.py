import serial
from serial.tools import list_ports
import asyncio
import struct
import sys
import numpy as np
import time
from multiprocessing.managers import BaseManager

class SerialPort(serial.Serial):
    """
    SerialPort is a compound class: both a serial.Serial and a publisher class. 
    Each port has a single subscriber connected to it; the class write/read from its serial port 
    and notify its subscriber when serial data is received.
    """
    # PUBLISHER-RELATED FUNCTIONS: to add listeners (subscribers) and 
    # notify them when new data is received.
    def subscribe(self, subscriber):
        self.listener = subscriber

    def notify(self, data):
        """
        Notify the subscriber (listener) that data has been received
        """
        # If data is a single 'int' then it's the battery level
        if isinstance(data,int): 
             self.listener.compute_battery_level(data)  
        else: 
            self.listener.update(data)
    
    # SERIAL-RELATED FUNCTIONS: read/write from BT port 
    def packets_stream(self, packet_length=27, batt_message_length=2):
        """
        Reads the stream of data transmitted by the serial port
        in packets of fixed lenght and data.
        Returns (acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, mag_x, mag_y, mag_z, quat_0, quat_1, quat_2, quat_3)
        """
        # Empties the buffer from the name of the sensor read by default
        self.readline()
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
                except: 
                    print("Couldn't read byte")
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
        self.batt_level = 0.0
        self.n_batt_updates = 0
        self.is_recording = False
        self.plot_data = np.zeros((9,25), dtype=np.float)  # Keeping the last 25 values to be plotted
        self.queue = np.empty((1,9), dtype=np.float) 

    def compute_battery_level(self, new_lvl):
        self.batt_level += new_lvl
        self.n_batt_updates += 1
        print(f"Battery percentage: {int(self.batt_level / self.n_batt_updates)} %")

    def update(self, data):
        # TODO: add packet processing here
        # Sensitivity values from Laura's code
        acc_sensitivity = (2.0 / 32768.0)  
        gyr_sensitivity = (250.0 / 32768.0)
        mag_sensitivity = (10. * 4800. / 32768.0)

        acc_array = np.array(data[0:3],dtype=np.float) * acc_sensitivity
        gyro_array = np.array(data[3:6], dtype=np.float) * gyr_sensitivity * np.pi/180  # Rad/s conversion
        mag_array = np.array(data[6:9], dtype=np.float) * mag_sensitivity

        # Update only stores packets in the queue when the flag (that can be set false by GUI) allows it    
        if self.is_recording:
            delta_time = time.time() 
            queue_item = np.concatenate((acc_array, gyro_array, mag_array), axis=None)
            self.queue = np.vstack((self.queue, queue_item))

            #Acc = [i * aRes for i in Acc] #porto dati nelle loro M.U
            #Acc_arr = np.array(Acc)

            """
                            Quat = [i/10000 for i in Quat] #in Arduino quat eramo stati moltiplicati per 1000 per mandare dati in int
                            Q = Quaternion(Quat)
                            inv_Q = Q.inverse
                            Acc_fixRF = Q.rotate(Acc_arr) #ruoto accelerazione in sist terrestre
                            Acc_lin_arr = np.subtract(Acc_fixRF,g_ideal) #sottraggo gravità
                            FreeAcc_bodyRF = inv_Q.rotate(Acc_lin_arr).tolist() #riporto in sistema del sensore
                            dt_real = Acc + Gyro + Mag + Quat + FreeAcc_bodyRF
                            dt_real.append(time.time())
                            count_values += 1
                            #seguente funzione è usata in caso non si stia registrando per resettare tabella in cui vengono messi i dati
                            #man mano che arrivano per non appesantire troppo la memoria
                            if rec_flag == False:
                                if count_values % 5400 == 0: #ogni circa 1 min viene resettata data_struct
                                    count_values = 0
                                    self.data_struct = {}
                                    for field in self.myFields:
                                        self.data_struct[field] = []
                            if flag_repetition_extraction == True:
                                self.repetition_extraction(exercise_name,dt_real) #solo per sensore da cui estraggo ripetizioni
                            for i, field in enumerate(self.data_struct.keys()):
                                self.data_struct[field].append(dt_real[i]) #aggiungo dati a data_struct
                            if position_called == self.position: #se il sensore è stato chiamato dalla GUI x visualizzazione
                                if data_sended_counter == 0:
                                    print(self.position+' start streaming')
                                data_sended_counter += 1
                                if self.data_receive.poll() == False:
                                    self.data_send.send(dt_real) #invio pacchetto di dati al Thread x visualizzazione       
                    else: #se leggo solo un dato --> batteria
                        if position_called == self.position:
                            self.battery_level_send.send(samp) #invio livello batteria x essere mostrato in GUI
            """


            print("Update received!")
            print(self.queue.shape)

        # The data is plotted even if the app is not recording data
        # Roll the array to append the data at the end of the array and
        # remove the first entry
        self.plot_data = np.roll(self.plot_data, -1, axis=1)
        self.plot_data[:3, -1] = acc_array
        self.plot_data[3:6, -1] = gyro_array
        self.plot_data[6:9, -1] = mag_array


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
        for port in ports[-3:]:
            try:
                if virtual_ports is None and port.device != "/dev/cu.Bluetooth-Incoming-Port":
                    # NOTE: timeout increased to 2 - was 1.5 - to avoid serial exceptions
                    ser = SerialPort(port=port.device, baudrate=57600, timeout=None, write_timeout=0)
                else:
                    #print("Connecting to virtual port(s)")
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

class MyManager(BaseManager):
    pass






