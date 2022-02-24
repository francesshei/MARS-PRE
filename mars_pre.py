from _serial import SerialPortManager, SerialPort
import time
from threading import Thread
from _threading import SerialReadingProcess, SerialWriterProcess
from _gui import MarsPreView
import ttkbootstrap as ttk
import threading

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

    for port in ports.keys():
        # Serial threads have to start before the application 
        # NOTE: this will continuously without the GUI interrupting them
        # The subscriber will be the one in charge to decide whether to save the data or not  
        thread = Thread(target=ports[port].packets_stream)
        thread.start()
    
    app = ttk.Window(
        title="MARS-PRE",
        themename="flatly",
        size=(350, 450),
        resizable=(True, True),
    )
    MarsPreView(app, spm=spm)
    app_thread = threading.Thread(target=app.mainloop())
    app_thread.start()
    app.mainloop()

