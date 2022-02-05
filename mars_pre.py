from _serial import SerialPortManager
import time
from _threading import SerialReadingProcess, SerialWriterProcess


if __name__ == '__main__':
    # Initialize a virtual serial port
    # Load a SPM, connect a subscriber to the port
    spm = SerialPortManager()
    ports = spm.load_ports(['/dev/ttys001'])
    print(ports)
    sr_process = SerialReadingProcess(ports['/dev/ttys001'])
    sr_process.start()



#ports = spm.load_ports()
#ports['BT-STERNUM-SPPDev'].write_to_serial('v')
#time.sleep(1)
#ports['BT-STERNUM-SPPDev'].start_stream()
