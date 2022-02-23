#TODO: implement a Model-View-Controller design pattern to handle the GUI. 
# The model acts as data-storage (roughly), the view is the front end (what the user sees)
# while the controller detects actions sent by the view and chooses the best strategy 
# See also: https://github.com/facebook/flux/tree/520a60c18aa3e9af59710d45cd37b9a6894a7bce/examples/flux-concepts

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.style import Bootstyle

import datetime
import pathlib
from queue import Queue
from threading import Thread
from tkinter.filedialog import askdirectory
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap import utility
import os
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

    def save_file(self, path, filename):
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
                                    
            with open(path + "/" + filename + ".csv", mode='w', newline="") as csv_file:
                nomicolonne = ['a', 'b', 'c']
                writer = csv.DictWriter(csv_file, fieldnames=nomicolonne)
                writer.writeheader()
                writer.writerow({'a': 'ciao', 'b': 'come', 'c': 'stai?'})
                writer.writerow({'a': 'hello', 'b': 'how', 'c': 'are you?'})
                print("Data saved in : " + path + filename)

            top = ttk.Toplevel()
            top.title('')

            _frame = ttk.Frame(top, padding = 25)
            _frame.pack(expand = NO, side=TOP)
            label = ttk.Label(_frame, text = "Data saved in : " + path +"/" + filename + ".csv", \
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
        bl_button = ttk.Button(bl_button_frame, text = "Test button", command=self.on_button_pressed, width=25,  bootstyle="secondary")
        bl_button.pack(fill=X, expand=YES)
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
        save_button = ttk.Button(fs_frame, text = "Save", command= lambda : self.controller.save_file(self.directory.get(),self.file.get()))
        save_button.pack()
      
    

    def create_sensors_list(self):
        # TODO: use port names instead of devices
        sensors_lables = {}
        calibration_buttons = {}
        #on_calibration = lambda port : self.controller.calibrate_sensor(port)
        """ Adding a list of sensors name as read by the serial port manager """
        for port in self.model.spm.ports_list:
            sensor_row = ttk.Frame(self.ss_lframe)
            sensor_row.pack(fill=X, expand=YES)
            label_text = port.device.split('-')[1].lower().capitalize() + ' ' + port.device.split('-')[2].lower() \
                        if len(port.device.split('-')[1]) <= 5 else port.device.split('-')[1].lower().capitalize()
            sensors_lables[port.device] = ttk.Label(sensor_row, text=label_text, width=25)
            sensors_lables[port.device].pack(side=LEFT, padx=(15, 0))
            calibration_buttons[port.device] = ttk.Button(sensor_row, text='Calibrate', command = lambda port = port.device : self.controller.calibrate_sensor(port), bootstyle="outline-secondary")
            calibration_buttons[port.device].pack()
    
    def on_button_pressed(self):
        # NOTE: debug purposes only
        for port in self.model.spm.ports_list[:3]:
            self.sensors_lables[port.device].config(foreground="gray")
            self.calibration_buttons[port.device].configure(state=DISABLED)

    



    