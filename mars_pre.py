from _gui import Model, View, Controller
import ttkbootstrap as ttk

"""
if __name__ == '__main__':
    # Initialize a virtual serial port
    # Load a SPM, connect a subscriber to the port
    spm = SerialPortManager()
    ports = spm.load_ports()
    
    # Initialize all the ports found from the SPM
    sensors_used = 0
    sensors_names = []
    for port in ports.keys():
        sensors_used += 1
        # Sending the first letter to have the port name 
        print(f"Writing to port: {port}")
        ports[port].write_to_serial('v')
        time.sleep(2)
        sensors_names.append(ports[port].check_port())
    
    if len(sensors_names) == sensors_used: 
        print("All sensors initialized successfully")
        #for i, port in enumerate(ports.keys()):
            # Serial threads have to start before the application 
            # NOTE: this will continuously without the GUI interrupting them
            # The subscriber will be the one in charge to decide whether to save the data or not  
        #    processes.append(Thread(target=ports[port].packets_stream))
        #    processes[i].start()

    # Creating the TKinter window 
    app = ttk.Window(
        title="MARS-PRE",
        themename="flatly",
        size=(350, 450),
        resizable=(True, True),
    )
    MarsPreView(app, spm=spm)
    # Launching the GUI app
    app.mainloop()
"""

class App(ttk.Window):
    def __init__(self):
        super().__init__(
        title="MARS-PRE",
        themename="flatly",
        size=(350, 450),
        resizable=(True, True))

        # Create a model
        model = Model()
        # Create a view and place it on the root window
        view = View(self)
        # Create a controller
        controller = Controller(view, model)
        # Set the controller to the view
        view.set_controller(controller)

# Start the application
if __name__ == '__main__':
    app = App()
    app.mainloop()