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
      
    

    def create_sensors_list(self):
        # TODO: use port names instead of devices
        self.sensors_lables = {}
        self.calibration_buttons = {}
        #on_calibration = lambda port : self.controller.calibrate_sensor(port)
        """ Adding a list of sensors name as read by the serial port manager """
        for port in self.model.spm.ports_list:
            sensor_row = ttk.Frame(self.option_lf)
            sensor_row.pack(fill=X, expand=YES)
            label_text = port.device.split('-')[1].lower().capitalize() + ' ' + port.device.split('-')[2].lower() \
                        if len(port.device.split('-')[1]) <= 5 else port.device.split('-')[1].lower().capitalize()
            self.sensors_lables[port.device] = ttk.Label(sensor_row, text=label_text, width=25)
            self.sensors_lables[port.device].pack(side=LEFT, padx=(15, 0))
            self.calibration_buttons[port.device] = ttk.Button(sensor_row, text='Calibrate', command = lambda port = port.device : self.controller.calibrate_sensor(port), bootstyle="outline-secondary")
            self.calibration_buttons[port.device].pack()
    
    def on_button_pressed(self):
        # NOTE: debug purposes only
        for port in self.model.spm.ports_list[:3]:
            self.sensors_lables[port.device].config(foreground="gray")
            self.calibration_buttons[port.device].configure(state=DISABLED)



    