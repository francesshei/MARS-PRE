#TODO: implement a Model-View-Controller design pattern to handle the GUI. 
# The model acts as data-storage (roughly), the view is the front end (what the user sees)
# while the controller detects actions sent by the view and chooses the best strategy 
# See also: https://github.com/facebook/flux/tree/520a60c18aa3e9af59710d45cd37b9a6894a7bce/examples/flux-concepts

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.style import Bootstyle

from multiprocessing import Process
from threading import Thread

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style

import time
import pathlib
from queue import Queue
from tkinter.filedialog import askdirectory
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap import utility
import os
import numpy as np
import csv


class MarsPreController():
    def __init__(self):
        pass

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

    def update_graph(self, model, axes, figure):
        ports = model.spm.ports
        port = list(ports.keys())[0]
        while True: 
            # Clear the graph to draw new data
            axes.cla()
            axes.set_ylim([-5,5])
            _font = {'family': 'sans-serif',
                    'color':  'black',
                    'weight': 'normal',
                    'size': 10,
            }
            axes.set_xlabel("Time", fontdict=_font)
            axes.set_ylabel("Acceleration", fontdict=_font)
            #axes.grid()
            # Retrieve the data to be plotted
            data = ports[port].listener[0].plot_data[1,:]
            axes.plot(range(25), data, marker='o', color='orange')
            figure.draw()
            time.sleep(0.001)

    
    def recording_button_pressed(self, model, view):
        ports = model.spm.ports
        if not model.recording:
            view.bl_button.configure(bootstyle='danger')
            view.bl_button.configure(text='Stop recording')
            model.recording = True
            for port in ports.keys():
                ports[port].listener[0].is_recording = True
        
        elif model.recording:
            view.bl_button.configure(bootstyle='success')
            view.bl_button.configure(text='Start recording')
            model.recording = False
            for port in ports.keys():
                ports[port].listener[0].is_recording = False

        # NOTE: debug purposes only
        #for port in self.model.spm.ports_list[:3]:
        #    self.sensors_lables[port.device].config(foreground="gray")
        #    self.calibration_buttons[port.device].configure(state=DISABLED)

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


class MarsPreModel():
    def __init__(self, spm):
        self.spm = spm
        self.recording = False


class MarsPreView(ttk.Frame):
    queue = Queue()
    searching = False

    def __init__(self, master, spm):
        super().__init__(master, padding=15)
        self.pack(fill=BOTH, expand=YES)
        self.model = MarsPreModel(spm)
        self.controller = MarsPreController()
        #  ----------------------------------------------------------------
        #  ----------------------------------------------------------------
        # Left column header container 
        self.outer_l_column = ttk.Frame(self)
        self.outer_l_column.pack(fill=Y, expand=NO, side=LEFT)
        #  ----------------------------------------------------------------
        # SpaceSensor labelled frame
        ss_lframe_label = "Available SpaceSens sensors:"
        self.ss_lframe = ttk.Labelframe(self.outer_l_column, text= ss_lframe_label, padding=15)
        self.ss_lframe.pack(side=TOP)
        self.create_sensors_list()
        # Sensors-related button 
        bl_button_frame = ttk.Frame(self.outer_l_column, padding=25)
        bl_button_frame.pack()
        self.bl_button = ttk.Button(bl_button_frame, text="Start recording", command= lambda model = self.model, view = self : self.controller.recording_button_pressed(model, view), width=25,  bootstyle="success")
        self.bl_button.pack(fill=X, expand=YES)
        #  ----------------------------------------------------------------
        # File saving 
        fs_label = "Store acquisition data:"
        fs_frame = ttk.Labelframe(self.outer_l_column, text= fs_label, padding=25)
        fs_frame.pack(side=TOP, expand=YES)
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
        save_button = ttk.Button(fs_frame, text = "Save", command= lambda : self.controller.save_file(self.directory.get(),self.file.get(),self.model))
        save_button.pack()
        #  ----------------------------------------------------------------
        # Plots section 
        self.plot_frame = ttk.Frame(self)
        self.plot_frame.pack(fill=X, expand=YES, side=RIGHT)
        
        # Create the figure
        figure = Figure(figsize=(6, 4), dpi=100)
        # Create the axes
        axes = figure.add_subplot()
        _grey_rgb = (197/255, 202/255, 208/255)
        axes.tick_params(color=_grey_rgb, labelcolor=_grey_rgb)
        for spine in axes.spines.values():
            spine.set_edgecolor(_grey_rgb)
        #axes.grid()

        # Create the FigureCanvasTkAgg widget and 
        # place it in the corresponding frame
        figure_canvas = FigureCanvasTkAgg(figure, self.plot_frame)
        figure_canvas.get_tk_widget().pack(fill=BOTH)

        #Start the thread to continuously update the plot
        Thread(target = lambda model = self.model, ax = axes, fig = figure_canvas: self.controller.update_graph(model,ax,fig)).start()

    def create_sensors_list(self):
        # TODO: use port names instead of devices
        sensors_lables = {}
        calibration_buttons = {}
        #on_calibration = lambda port : self.controller.calibrate_sensor(port)
        """ Adding a list of sensors name as read by the serial port manager """
        for port in self.model.spm.ports_list:
            sensor_row = ttk.Frame(self.ss_lframe, padding = 5)
            sensor_row.pack(fill=X, expand=YES)
            label_text = port.device.split('-')[1].lower().capitalize() + ' ' + port.device.split('-')[2].lower() \
                        if len(port.device.split('-')[1]) <= 5 else port.device.split('-')[1].lower().capitalize()
            sensors_lables[port.device] = ttk.Label(sensor_row, text=label_text, width=25)
            sensors_lables[port.device].pack(side=LEFT, padx=(15, 0))
            calibration_buttons[port.device] = ttk.Button(sensor_row, text='Calibrate', command = lambda port = port.device : self.controller.calibrate_sensor(port), bootstyle="outline-secondary")
            calibration_buttons[port.device].pack()
    

    



    