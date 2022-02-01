from _serial import SerialPortManager
import time

spm = SerialPortManager()
ports = spm.load_ports()


ports['BT-STERNUM-SPPDev'].write_to_serial('v')
time.sleep(1)
ports['BT-STERNUM-SPPDev'].start_stream()
