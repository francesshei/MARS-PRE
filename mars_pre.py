from _serial import SerialPortManager, SerialPort
import time
from multiprocessing import Process
from _threading import SerialReadingProcess, SerialWriterProcess
from _gui import MarsPreView
import ttkbootstrap as ttk

if __name__ == '__main__':
    # Initialize a virtual serial port
    # Load a SPM, connect a subscriber to the port
    spm = SerialPortManager()
    ports = spm.load_ports()
    
    # Initialize all the ports found from the SPM
    # (following Laura's code)
    for port in ports.keys():
        # Sending the first letter to have the port name 
        print(f"Writing to port: {port}")
        ports[port].write_to_serial('v')
        time.sleep(2)
        print(ports[port].check_port())
    
    # Starting to read data continuously
    for port in ports.keys():
        print("Starting buffer reading")
        # Start a process that will run the "SerialPort.chuncked_stream" 
        # function 
        sr_process = Process(target=ports[port].packets_stream())
        #sr_process.start()
    
    app = ttk.Window(
        title="MARS-PRE",
        themename="flatly",
        size=(350, 450),
        resizable=(True, True),
    )
    MarsPreView(app, spm=spm)
    app.mainloop()

