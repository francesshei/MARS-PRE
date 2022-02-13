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
        print(f"Calibrating {port}")

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

        # Left column header container 
        self.outer_left_column = ttk.Frame(self)
        self.outer_left_column.pack(fill=Y, expand=NO, side=LEFT)

        option_text = "Available SpaceSens sensors:"
        self.option_lf = ttk.Labelframe(self.outer_left_column, text= option_text, padding=15)
        self.option_lf.pack(side=TOP)
        
        _bl_button_frame = ttk.Frame(self.outer_left_column, padding=25)
        _bl_button_frame.pack()
        _bl_button = ttk.Button(_bl_button_frame, text = "Test button", command=self.on_button_pressed, bootstyle="outline")
        _bl_button.pack(fill=X, expand=YES)
        self.create_sensors_list()
        self.directory()
      
    

    def create_sensors_list(self):
        # TODO: use port names instead of devices
        self.sensors_lables = {}
        self.calibration_buttons = {}
        #on_calibration = lambda port : self.controller.calibrate_sensor(port)
        """ Adding a list of sensors name as read by the serial port manager """
        for port in self.model.spm.ports_list:
            sensor_row = ttk.Frame(self.option_lf)
            sensor_row.pack(fill=X, expand=YES)
            # label_text = port.device.split('-')[1].lower().capitalize() + ' ' + port.device.split('-')[2].lower() \
            #             if len(port.device.split('-')[1]) <= 5 else port.device.split('-')[1].lower().capitalize()
            self.sensors_lables[port.device] = ttk.Label(sensor_row, text=port.device, width=25)
            self.sensors_lables[port.device].pack(side=LEFT, padx=(15, 0))
            self.calibration_buttons[port.device] = ttk.Button(sensor_row, text='Calibrate', command = lambda port = port.device : self.controller.calibrate_sensor(port), bootstyle="outline-secondary")
            self.calibration_buttons[port.device].pack()
    
    def on_button_pressed(self):
        # NOTE: debug purposes only
        for port in self.model.spm.ports_list[:3]:
            self.sensors_lables[port.device].config(foreground="gray")
            self.calibration_buttons[port.device].configure(state=DISABLED)


    def directory(self):

        option_text = "Saving data:"
        _frame = ttk.Labelframe(self.outer_left_column, text= option_text, padding=25)
        _frame.pack(side=TOP)

        entry1_row = ttk.Frame(_frame)
        entry1_row.pack(fill=X, expand=YES)

        name_dir = ttk.Label(entry1_row, text = 'Directory :')
        name_dir.pack(side=LEFT, expand=YES, pady = 5, padx = 8)

        self._directory = ttk.StringVar()
        entry1 = ttk.Entry(entry1_row, textvariable = self._directory, width=30)
        entry1.insert(END,"C:/Users/feder/Desktop")
        entry1.pack(side=LEFT, expand=YES,pady = 5)

        entry2_row = ttk.Frame(_frame)
        entry2_row.pack(fill=X, expand=YES)

        name_file = ttk.Label(entry2_row, text = 'File Name :')
        name_file.pack(side=LEFT, expand=YES, padx = 5, pady =5)

        self.file = ttk.StringVar()
        entry2 = ttk.Entry(entry2_row, textvariable = self.file, width=30)
        entry2.insert(END,"data")
        entry2.pack(side=LEFT, expand=YES,pady = 5)

        _bl_button_frame = ttk.Frame(self.outer_left_column, padding=25)
        _bl_button_frame.pack()
        _bl_button = ttk.Button(_bl_button_frame, text = "Save", command=self.on_button_pressed, bootstyle="outline")
        _bl_button.pack(fill=X, expand=YES)

    def on_button_pressed(self):

        _path=self._directory.get()
        file_name=self.file.get()   

        if not _path or not file_name:
  
            top = ttk.Toplevel()
            top.title('WARNING')

            _frame = ttk.Frame(top, padding = 25)
            _frame.pack(expand = NO, side=TOP)
            label = ttk.Label(_frame, text = "Fill the required fields !")
            label.pack(expand = NO)

            _but = ttk.Frame(top, padding = 15)
            _but.pack(expand = NO, side=TOP)
            but = ttk.Button(_but, text = 'Quit', command = top.destroy, bootstyle="outline")
            but.pack(expand = NO)   

            top.transient()
            top.grab_set()

        elif not os.path.isdir(_path): 
            
            top = ttk.Toplevel()
            top.title("WARNING")

            _frame = ttk.Frame(top, padding = 25)
            _frame.pack(expand = NO, side=TOP)
            label = ttk.Label(_frame, text = "Directory not found")
            label.pack(expand = NO)

            _but = ttk.Frame(top, padding = 15)
            _but.pack(expand = NO, side=TOP)
            but = ttk.Button(_but, text = 'Quit', command = top.destroy, bootstyle="outline")
            but.pack(expand = NO)   

            top.transient()
            top.grab_set()
           
        else:   
                                    
            with open(_path + "/" + file_name + ".csv", mode='w', newline="") as csv_file:
                nomicolonne = ['a', 'b', 'c']
                writer = csv.DictWriter(csv_file, fieldnames=nomicolonne)
                writer.writeheader()
                writer.writerow({'a': 'ciao', 'b': 'come', 'c': 'stai?'})
                writer.writerow({'a': 'hello', 'b': 'how', 'c': 'are you?'})
                print("Data saved in : " + _path + file_name)

            top = ttk.Toplevel()
            top.title('')

            _frame = ttk.Frame(top, padding = 25)
            _frame.pack(expand = NO, side=TOP)
            label = ttk.Label(_frame, text = "Data saved in : " + _path +"/" + file_name + ".csv", \
                                            wraplength=220, anchor=ttk.NW, justify=ttk.LEFT)
            label.pack(expand = NO)

            _but = ttk.Frame(top, padding = 15)
            _but.pack(expand = NO, side=TOP)
            but = ttk.Button(_but, text = 'Quit', command = top.destroy, bootstyle = "outline")
            but.pack(expand = NO)   

            top.transient()
            top.grab_set()

