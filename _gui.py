#TODO: implement a Model-View-Controller design pattern to handle the GUI. 
# The model acts as data-storage (roughly), the view is the front end (what the user sees)
# while the controller detects actions sent by the view and chooses the best strategy 
# See also: https://github.com/facebook/flux/tree/520a60c18aa3e9af59710d45cd37b9a6894a7bce/examples/flux-concepts

from turtle import listen
import ttkbootstrap as ttk
from tkinter import PhotoImage
from ttkbootstrap import utility
from ttkbootstrap.constants import *
from ttkbootstrap.style import Bootstyle

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import time
import os
import numpy as np
from threading import Thread
from multiprocessing import Process

from _serial import SerialSubscriber, SerialPort, SerialProcessManager
from serial.tools import list_ports


class Controller():
    def __init__(self, view, model):
        self.view = view 
        self.model = model
        self.recording = False 
    
    def create_sensors_list(self):
        # TODO: use port names instead of devices
        #calibration_buttons = {}
        # Adding a list of sensors name as read by the serial port manager
        for device in self.model.ports_list:
        #for device in self.model.spm.ports_list:
            port = device.device 
            sensor_row = ttk.Frame(self.view.ss_frame, padding = 5)
            sensor_row.pack(fill=X, expand=YES)
            label_text = port.split('-')[1].lower().capitalize() + ' ' + port.split('-')[2].lower() \
                        if len(port.split('-')[1]) <= 5 else port.split('-')[1].lower().capitalize()
            _label = ttk.Label(sensor_row, text=label_text, width=15)
            _label.pack(side=LEFT)
            _connect_button = ttk.Button(sensor_row, text='Connect', command = lambda port = port : self.connect_sensor(port), bootstyle="primary")
            _connect_button.pack(side=LEFT, padx=(15, 0))
            _calibration_button = ttk.Button(sensor_row, text='Calibrate', command = lambda port = port : self.calibrate_sensor(port), bootstyle="outline-secondary")
            _calibration_button.pack(padx=(15, 0))
    
    def connect_sensor(self, port):
        self.model.start_serial_process(port)

    def calibrate_sensor(self, port):
        # TODO: send calibration command to sensors 
        """
        From Laura's code:
        if self.readable_magcal_pipes[self.position].poll():
                data_cal = self.readable_magcal_pipes[self.position].recv() #ricevo info su ricalibrazione mag
                if data_cal == 'start calibration':
                    self.ser.write(b'b') #invio carattere ad Arduino per informarlo del voler fare ricalibrazione 
                else:
                    print(data_cal) #al termine della calibrazione ottendgo valori di bias e scale
                    data_send = data_cal+'\n'
                    self.ser.write(data_send.encode()) #invio valori ad Arduino per salvarli nei registri 
        """
        print(f"Calibrating {port}")
    
    """
    def update_graph(self, model, figure, canvas):
        ports = model.spm.ports
        port = list(ports.keys())[0]
        _grey_rgb = (197/255, 202/255, 208/255)
        _font = {'family': 'sans-serif',
                    'color':  'black',
                    'weight': 'normal',
                    'size': 10,
            }

        # Create the axes
        # IMU
        acc_axes = figure.add_subplot(311)
        acc_axes.tick_params(color=_grey_rgb, labelcolor=_grey_rgb)
        for spine in acc_axes.spines.values():
            spine.set_edgecolor(_grey_rgb)
        # Gyroscope
        gyr_axes = figure.add_subplot(312)
        gyr_axes.tick_params(color=_grey_rgb, labelcolor=_grey_rgb)
        for spine in gyr_axes.spines.values():
            spine.set_edgecolor(_grey_rgb)
        # Magnetometer
        mag_axes = figure.add_subplot(313)
        mag_axes.tick_params(color=_grey_rgb, labelcolor=_grey_rgb)
        for spine in mag_axes.spines.values():
            spine.set_edgecolor(_grey_rgb)
        
        while True: 
            # Retrieve the data to be plotted
            data = ports[port].listener[0].plot_data
            # Clear the graph to draw new data
            # IMU 
            acc_axes.cla()
            acc_axes.set_ylim([-5,5])
            #acc_axes.set_xlabel("Time", fontdict=_font)
            acc_axes.set_ylabel("Accelerometer \n data", fontdict=_font)
            acc_axes.plot(range(25), data[0,:], marker='o', label='x')
            acc_axes.plot(range(25), data[1,:], marker='o', label='y')
            acc_axes.plot(range(25), data[2,:], marker='o', label='z')
            acc_axes.legend()

            # Gyroscope
            gyr_axes.cla()
            gyr_axes.set_ylim([-10,10])
            #acc_axes.set_xlabel("Time", fontdict=_font)
            gyr_axes.set_ylabel("Gyroscope \n data", fontdict=_font)
            gyr_axes.plot(range(25), data[3,:], marker='o', label='x')
            gyr_axes.plot(range(25), data[4,:], marker='o', label='y')
            gyr_axes.plot(range(25), data[5,:], marker='o', label='z')
            gyr_axes.legend()

            # Magnetometer  
            mag_axes.cla()
            mag_axes.set_ylim([-20,20])
            #acc_axes.set_xlabel("Time", fontdict=_font)
            mag_axes.set_ylabel("Magentometer \n data", fontdict=_font)
            mag_axes.plot(range(25), data[6,:], marker='o', label='x')
            mag_axes.plot(range(25), data[7,:], marker='o', label='y')
            mag_axes.plot(range(25), data[8,:], marker='o', label='z')
            mag_axes.legend()

            # Finally, re-draw the canvas
            canvas.draw()
            time.sleep(0.001)
    """
    
    def record(self):
        ports = self.model.spm.ports()
        listeners = self.model.spm.listeners()
        if not self.recording:
            self.view.bl_button.configure(bootstyle='danger')
            self.view.bl_button.configure(text='Stop recording')
            self.recording = True
            for port in ports.keys():
                self.model.spm.set_listener_active(port)
                #listeners[port].is_recording = True
                print("Getting data:")
                print(listeners[port].update_plot_data())
                #print(ports[port].listener)
        
        elif self.recording:
            self.view.bl_button.configure(bootstyle='success')
            self.view.bl_button.configure(text='Start recording')
            self.recording = False
            for port in ports.keys():
                self.model.spm.ports()[port].listener.is_recording = False

        # NOTE: debug purposes only
        #for port in self.model.spm.ports_list[:3]:
        #    self.sensors_lables[port.device].config(foreground="gray")
        #    self.calibration_buttons[port.device].configure(state=DISABLED)
    """
    def save_file(self, path, filename, model):
        ports = model.spm.ports
        if not path or not filename:
            # Pop-up warning window
            top = ttk.Toplevel()
            top.title('WARNING')

            _frame = ttk.Frame(top, padding = 25)
            _frame.pack(expand = NO, side=TOP)
            label = ttk.Label(_frame, text = "Please, fill the required fields!")
            label.pack(expand = NO)

            _but = ttk.Frame(top, padding = 15)
            _but.pack(expand = NO, side=TOP)
            but = ttk.Button(_but, text = 'Okay', command = top.destroy, bootstyle="outline-warning")
            but.pack(expand = NO)   

            top.transient()
            top.grab_set()

        elif not os.path.isdir(path): 
            
            top = ttk.Toplevel()
            top.title("WARNING")

            _frame = ttk.Frame(top, padding = 25)
            _frame.pack(expand = NO, side=TOP)
            label = ttk.Label(_frame, text = "Directory not found!")
            label.pack(expand = NO)

            _but = ttk.Frame(top, padding = 15)
            _but.pack(expand = NO, side=TOP)
            but = ttk.Button(_but, text = 'Quit', command = top.destroy, bootstyle="outline-warning")
            but.pack(expand = NO)   

            top.transient()
            top.grab_set()
           
        else: 
            for port in ports.keys():
                np.savetxt(
                    f"{path}/{filename}-{port.split('/')[-1]}.csv", 
                    ports[port].listener[0].queue[1:], 
                    delimiter=',', 
                    header="Acc_x,Acc_y,Acc_z,Gyro_x,Gyro_y,Gyro_z,Mag_x,Mag_y,Mag_z", 
                    comments="")     

            #with open(path + "/" + filename + ".csv", mode='w', newline="") as csv_file:
            #    nomicolonne = ['a', 'b', 'c']
            #    writer = csv.DictWriter(csv_file, fieldnames=nomicolonne)
            #    writer.writeheader()
            #    writer.writerow({'a': 'ciao', 'b': 'come', 'c': 'stai?'})
            #    writer.writerow({'a': 'hello', 'b': 'how', 'c': 'are you?'})
            #print(f"Data saved in {path}/{filename}-{port.split('/')[-1]}.csv")

            top = ttk.Toplevel()
            top.title('')

            _frame = ttk.Frame(top, padding = 25)
            _frame.pack(expand = NO, side=TOP)
            label = ttk.Label(_frame, text = f"Data saved in {path}/{filename}-{port.split('/')[-1]}.csv", \
                                            wraplength=220, anchor=ttk.NW, justify=ttk.LEFT)
            label.pack(expand = NO)

            _but = ttk.Frame(top, padding = 15)
            _but.pack(expand = NO, side=TOP)
            but = ttk.Button(_but, text = 'Okay', command = top.destroy, bootstyle = "outline-success")
            but.pack(expand = NO)   

            top.transient()
            top.grab_set()
    """

class Model():
    """
    The model act as a serial port manager: mantains an array of processes, 
    each controlling a SerialPort object for all connected sensors. 
    Each SerialPort manages its messages (transmitting / receiving); the
    SerialPortManager implements the interrupt (e.g., when closing the program)
    """
    def __init__(self, spm):
        self.ports_list = [port for port in list_ports.comports()]
        self.ports = []
        self.spm = spm.SPM()
        
        """ 
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
        
        """
    def start_serial_process(self, port):
        p = Process(target=self.setup_port,args=(port,))
        print("Starting process")
        p.start()
        print("Process started")

    def setup_port(self, port):
        try:
            s = SerialSubscriber()
            ser = SerialPort(port, subscriber=s)
            if ser.is_open:
                #print("Initializing port subscriber")
                print(f"Adding port to SPM")
                self.spm.set_port(ser)
                #listener = SerialSubscriber()
                #ser.subscribe(listener)
                #print(f"Adding port to SPM")
                #self.spm.set_port(ser, listener)
                print("Port added to SPM")
                # Bootstrapping the Arduino firmware loop
                ser.write_to_serial('v')
            ser.packets_stream()
        except Exception as e: 
            print(f"Could not connect to port: {port}, {e}")



class View(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=15, bootstyle="light")
        self.pack(fill=BOTH, expand=YES)
        self.controller = None
        # Icons and images
        self.icons = [PhotoImage(name='asi', 
                file='./icons/ASI.png'),
                    PhotoImage(name='iss', 
                file='./icons/ISS.png')
            ]
        #  ----------------------------------------------------------------
        #  ----------------------------------------------------------------
        # Left column header container 
        self.outer_l_column = ttk.Frame(self, bootstyle="light")
        self.outer_l_column.pack(fill=Y, expand=NO, side=LEFT)
        #  ----------------------------------------------------------------
        # SpaceSensor labelled frame
        self.ss_frame = ttk.Frame(self.outer_l_column, padding=25)
        self.ss_frame.pack()
        ss_lframe_label = ttk.Label(self.ss_frame, text="Available SpaceSens sensors:", font="-size 18 -weight bold")
        ss_lframe_label.pack()
        # Sensors-related button 
        bl_button_frame = ttk.Frame(self.outer_l_column, padding=25)
        bl_button_frame.pack()
        self.bl_button = ttk.Button(self.ss_frame, text="Start recording", command=self.recording_button_pressed, width=25,  bootstyle="success")
        self.bl_button.pack(fill=X, side=BOTTOM, expand=NO)
        #  ----------------------------------------------------------------
        # File saving 
        fs_frame = ttk.Frame(self.outer_l_column, padding=25)
        fs_frame.pack(side=TOP, expand=YES)
        fs_label = ttk.Label(fs_frame, text= "Store acquisition data:", font="-size 18 -weight bold")
        fs_label.pack()
        # First text input row
        entry1_row = ttk.Frame(fs_frame)
        entry1_row.pack(fill=Y, expand=YES)
        # Directory entry input label 
        name_dir = ttk.Label(entry1_row, text = 'Directory:')
        name_dir.pack(side=TOP, expand=NO, padx=8)
        # Directory entry input 
        self.directory = ttk.StringVar()
        entry1 = ttk.Entry(entry1_row, textvariable = self.directory, width=30)
        entry1.insert(END,os.getcwd())
        entry1.pack(side=BOTTOM, expand=YES, pady=5)
        # Second text input row
        entry2_row = ttk.Frame(fs_frame)
        entry2_row.pack(fill=Y, expand=YES)
        # Filename entry input label
        name_file = ttk.Label(entry2_row, text = 'File Name:')
        name_file.pack(side=TOP, expand=YES, padx=8)
        # Filename entry input  
        self.file = ttk.StringVar()
        entry2 = ttk.Entry(entry2_row, textvariable = self.file, width=30)
        entry2.insert(END,"data")
        entry2.pack(side=BOTTOM, expand=YES, pady=5)
        # Save button
        #save_button = ttk.Button(fs_frame, text = "Save", command= lambda : self.controller.save_file(self.directory.get(),self.file.get(),self.model))
        #save_button.pack()
        
        #Label container 
        labels_container = ttk.Frame(self.outer_l_column, bootstyle="light", padding=25)
        labels_container.pack(side=BOTTOM, fill=BOTH, expand=NO)
        iss = ttk.Label(labels_container, bootstyle="inverse-light", image='iss').pack(fill=X, pady=5, side=RIGHT)
        asi = ttk.Label(labels_container, bootstyle="inverse-light", image='asi').pack(fill=X, pady=5, side=RIGHT)
        #  ----------------------------------------------------------------
        # Plots section 
        outer_r_column = ttk.Frame(self, bootstyle="light")
        outer_r_column.pack(fill=BOTH, expand=YES, side=RIGHT)
        # Logos
        #asi = ttk.Label(outer_r_column, bootstyle="inverse-light", image='asi').pack(fill=X, pady=5, side=RIGHT)

        self.plot_frame = ttk.Frame(outer_r_column, padding = 25)
        self.plot_frame.pack(fill=BOTH, expand=YES, padx=8)

        # Data label
        data_label = ttk.Label(self.plot_frame, text= "SpaceSens data plots", font="-size 18 -weight bold").pack(fill=X)
        
        # Create the figure
        figure = Figure(figsize=(15, 8), dpi=150)
        # Create the FigureCanvasTkAgg widget and 
        # place it in the corresponding frame
        figure_canvas = FigureCanvasTkAgg(figure, self.plot_frame)
        figure_canvas.get_tk_widget().pack(fill=BOTH,  expand=YES)

        # Start the thread to continuously update the plot
        #Thread(target = lambda model = self.model, fig = figure, canvas = figure_canvas: self.controller.update_graph(model,fig,canvas)).start()
    
    def set_controller(self, controller):
        self.controller = controller
        # Once the controller is set, sensors can be inserted in the view  
        self.controller.create_sensors_list()
    
    def recording_button_pressed(self):
        if self.controller:
            self.controller.record()

    

    



    