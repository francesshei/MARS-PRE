import serial
from serial.tools import list_ports
import struct
from multiprocessing import Process


def packets_stream(ser, packet_length=27, batt_message_length=2):
    """
    Reads the stream of data transmitted by the serial port
    in packets of fixed lenght and data.
    Returns (acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, mag_x, mag_y, mag_z, quat_0, quat_1, quat_2, quat_3)
    """
    print("Process started")
    # Empties the buffer from the name of the sensor read by default
    ser.readline()
    # Initializing quantities needed for serial reading
    b = b''
    h = t = count = 0 
    raw_data = []
    batt_lvl_data = []
    while True:
        # Look for the packet header (0xA0)
        while h != 0xa0:
            b = ser.read(1)
            print(b)
            if len(b)>0:
                h = b[0]
            # Battery level is sent among the packets with a different header
                if h == 0xf0:
                    while t != 0xff and count <= batt_message_length:
                        b = ser.read(1)
                        batt_lvl_data.append(b)
                        if len(b)>0:
                            t = b[0]
                        count += 1
                    # Unpack the battery level unsigned int and notify the subscriber
                    batt_lvl = struct.unpack('Bx', b''.join(batt_lvl_data))[0]
                    #self.notify(batt_lvl)
                    batt_lvl_data = []
                    t = 0 
        count = 1
        # Once found, read until the packet tail (0xC0)
        # or until the end of the expected packet length
        while h != 0xc0 or count <= packet_length:
            try: 
                b = ser.read(1)
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
            #self.notify(list(data))
            #print("Packet received")
            #print(f"Data: {data}, {type(data)}")
        
        # Re-initialize the variables to read the next packet
        data = raw_data = []
        count = 0
        b = 0 

def start_port(port):
    try:
        ser = serial.Serial(port=port.device, baudrate=57600, timeout=None, write_timeout=0)
        print(f"Port {port.device} open") 
        ser.write('v'.encode('utf8'))
        print("Wrote to port")
    except: 
        print(f"Failed to open port {port.device}")
    packets_stream(ser, packet_length=27, batt_message_length=2)


if __name__ == "__main__":
    ports_list = [port for port in list_ports.comports()]
    for port in ports_list[-1:]:
        #start_port(port)
        p = Process(target=start_port,args=(port,))
        print("Starting process")
        p.start()