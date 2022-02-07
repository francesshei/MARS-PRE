from _serial import SerialPortManager, SerialPort
import time
from multiprocessing import Process
from _threading import SerialReadingProcess, SerialWriterProcess


if __name__ == '__main__':
    # Initialize a virtual serial port
    # Load a SPM, connect a subscriber to the port
    spm = SerialPortManager()
    ports = spm.load_ports()

    for port in ports.keys():
        print(f"Writing to port: {port}")
        ports[port].write_to_serial('v')
        time.sleep(2)
        print("Starting buffer reading")
        print(ports[port].check_port())
        #print(check)
        time.sleep(2)
        sr_process = Process(target = ports[port].chunked_stream())
        sr_process = SerialReadingProcess(spm)
        #sr_process.start()



#ports = spm.load_ports()
#ports['BT-STERNUM-SPPDev'].write_to_serial('v')
#time.sleep(1)
#ports['BT-STERNUM-SPPDev'].start_stream()
