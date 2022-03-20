import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from tkinter import PhotoImage
from ttkbootstrap.constants import *

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.signal import find_peaks

import time
import os, signal
import numpy as np
from threading import Thread
from multiprocessing import Process

from _serial import SerialSubscriber
from serial.tools import list_ports


class Controller():
    def __init__(self, view, model):
        self.view = view 
        self.model = model
        self.recording = False 
        self.tuning = False
    
    def create_sensors_list(self):
        # TODO: use port names instead of devices
        #calibration_buttons = {}
        # Adding a list of sensors name as read by the serial port manager
        for device in self.model.ports_list:
        #for device in self.model.spm.ports_list:
            port = device.device 
            sensor_row = ttk.Frame(self.view.scrolls_frame, padding=5, bootstyle="dark")
            sensor_row.pack(fill=X, expand=YES,  pady=5)
            if len(port.split('-'))>1:
                position = port.split('-')[1].lower().capitalize() # Extracting the name of the sensor from its port definition
                body_part = port.split('-')[2].lower()
                if len(port.split('-')[1]) <= 5:
                    if body_part == 'tight':
                        body_part = 'thigh'
                    label_text = f"{position} {body_part}"
                else:
                    label_text = f"{position}"
            else: 
                label_text = port
            _label = ttk.Label(sensor_row, text=label_text, width= 10, bootstyle="inverse-dark")
            _label.config(foreground="gray")
            _label.pack(side=LEFT)

            _calibration_button = ttk.Button(sensor_row, text='Calibrate', command = lambda port=port : self.calibrate_sensor(port), bootstyle="outline-secondary")
            _connect_button = ttk.Button(sensor_row, text='Connect', command = lambda port=port, label=_label, cal_button=_calibration_button: self.connect_sensor(port, label,cal_button), bootstyle="outline-primary")
            _connect_button.pack(side=LEFT, padx=(15, 0))
            # _calibration_button defined above to pass it to _connect_button
            _calibration_button.pack(padx=(15, 0))
            _calibration_button.configure(state=DISABLED)
    
    def connect_sensor(self, port, label, cal_button):
        self.model.start_serial_port(port)
        # Set the port
        if port.split('-')[1].lower().capitalize()=='Pelvis': # Deadlift port (exercise type = 1)
            self.model.exercise_ports[1] = port
        if port.split('-')[1].lower().capitalize()=='Right' and port.split('-')[2].lower()=='tight': # Squats port (exercise type = 1)
            self.model.exercise_ports[2] = port
        # Activate the label and the calibration button
        label.config(foreground="white")
        cal_button.configure(state=ACTIVE)
        if str(self.view.quit_button['state']) == 'disabled':
            self.view.quit_button.configure(state=ACTIVE)
        # Create a frame and add it to the notebook widget
        plot_frame = ttk.Frame(self.view.notebook)
        # TODO clean the notebook text
        self.view.notebook.add(plot_frame, text=port)
        # Place the meter on the frame
        _meter = ttk.Meter(
            master=plot_frame,
            metersize=150,
            amountused=None,
            subtext="Battery level",
            bootstyle="light",
            interactive=False,
            padding=15)
        _meter.pack()
        # Create the figure
        figure = Figure(figsize=(15, 8), dpi=100)
        figure.patch.set_facecolor('#222222')
        # Create the FigureCanvasTkAgg widget and 
        # place it in the corresponding frame
        figure_canvas = FigureCanvasTkAgg(figure, plot_frame)
        figure_canvas.get_tk_widget().pack(fill=BOTH,  expand=YES)
        Thread(target = lambda fig=figure, canvas=figure_canvas, port=port, meter=_meter: self.update_graph(fig,canvas, port, meter)).start()

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

    def grab_tuning_data(self):
        ports = self.model.ports
        exercise_ports = self.model.exercise_ports
        exercise_type = self.model.exercise_type

        if exercise_type is not None:
            if not self.tuning:
                try: 
                    ports[exercise_ports[exercise_type]].clear_queue()
                    ports[exercise_ports[exercise_type]].start_recording()
                    self.view.tuning_monitor_button.configure(bootstyle='danger')
                    self.view.tuning_monitor_button.configure(text='Stop acquiring')
                    self.tuning = True
                except: 
                    print("Add corresponding sensor for tuning: right thigh for squats, pelvis for deadlift")
            
            elif self.tuning:
                self.view.tuning_monitor_button.configure(bootstyle='primary')
                self.view.tuning_monitor_button.configure(text='Acquire tuning data')
                self.tuning = False
                ports[exercise_ports[exercise_type]].stop_recording()
                self.model.update_exercise_quantities(ports[exercise_ports[exercise_type]].listener.queue[1:])

    def update_exercise_type(self, exercise):
        self.model.exercise_type = exercise
    
    def update_graph(self, figure, canvas, port, meter):
        ports = self.model.ports
        if len(ports) > 0: 
            #port = list(ports.keys())[0]
            _grey_rgb = (197/255, 202/255, 208/255)
            _font = {   'family': 'sans-serif',
                        'color':  'white',
                        'weight': 'normal',
                        'size': 10,
                }
            n_samples = 1000
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
                try:
                    # Retrieve the data to be plotted
                    data = ports[port].update_plot_data()
                    battery = ports[port].update_batt_lvl()
                    # Update the meter values
                    meter.configure(amountused=battery)
                    # Clear the graph to draw new data
                    # IMU 
                    acc_axes.cla()
                    acc_axes.set_ylim([-5,5])
                    #acc_axes.set_xlabel("Time", fontdict=_font)
                    acc_axes.set_ylabel("Accelerometer \n data", fontdict=_font)
                    acc_axes.set_facecolor('#222222')
                    acc_axes.plot(range(n_samples), data[0,:], label='x', color='#299CB1')
                    acc_axes.plot(range(n_samples), data[1,:], label='y', color='#18B179')
                    acc_axes.plot(range(n_samples), data[2,:], label='z', color='#825194')
                    acc_axes.legend(loc='upper right')

                    # Gyroscope
                    gyr_axes.cla()
                    gyr_axes.set_ylim([-10,10])
                    #acc_axes.set_xlabel("Time", fontdict=_font)
                    gyr_axes.set_ylabel("Gyroscope \n data", fontdict=_font)
                    gyr_axes.set_facecolor('#222222')
                    gyr_axes.plot(range(n_samples), data[3,:], label='x', color='#299CB1')
                    gyr_axes.plot(range(n_samples), data[4,:], label='y', color='#18B179')
                    gyr_axes.plot(range(n_samples), data[5,:], label='z', color='#825194')
                    gyr_axes.legend(loc='upper right')

                    # Magnetometer  
                    mag_axes.cla()
                    mag_axes.set_ylim([-20,20])
                    #acc_axes.set_xlabel("Time", fontdict=_font)
                    mag_axes.set_ylabel("Magentometer \n data", fontdict=_font)
                    mag_axes.set_facecolor('#222222')
                    mag_axes.plot(range(n_samples), data[6,:], label='x', color='#299CB1')
                    mag_axes.plot(range(n_samples), data[7,:], label='y', color='#18B179')
                    mag_axes.plot(range(n_samples), data[8,:], label='z', color='#825194')
                    mag_axes.legend(loc='upper right')

                    # Finally, re-draw the canvas
                    canvas.draw()
                    time.sleep(0.01)
                except Exception as e:
                    print(e) 
    
    def record(self):
        ports = self.model.ports
        
        if not self.recording:
            self.view.bl_button.configure(bootstyle='danger')
            self.view.bl_button.configure(text='Stop recording')
            self.recording = True
            for port in ports.keys():
                ports[port].clear_queue()
                ports[port].start_recording()
        
        elif self.recording:
            self.view.bl_button.configure(bootstyle='success')
            self.view.bl_button.configure(text='Start recording')
            self.recording = False
            for port in ports.keys():
                ports[port].stop_recording()
    
    def save_file(self, path, filename):
        self.model.write_file(path, filename)

    def quit(self):
        nb = self.view.notebook
        #def deletetab():
        for item in nb.winfo_children():
            if str(item) == (nb.select()):
                #print(nb.select())
                item.destroy()
                return  #Necessary to break or for loop can destroy all the tabs when first tab is deleted


        #self.view.destroy()
        #print("Terminating background processes...")
        #for pid in self.model.process_ids:
        #    os.kill(pid, signal.SIGKILL)
        #print("All serial processes terminated")
        #exit()


class Model():
    """
    The model act as a serial port manager: mantains an array of processes, 
    each controlling a SerialPort object for all connected sensors. 
    Each SerialPort manages its messages (transmitting / receiving); the
    SerialPortManager implements the interrupt (e.g., when closing the program)
    """
    def __init__(self, spm):
        self.ports_list = [port for port in list_ports.comports()]
        self.ports = {}
        self.exercise_type = None
        self.exercise_ports = {}
        self.squat_port = self.deadlift_port = None 
        self.process_ids = []
        self.spm = spm 

    def start_serial_port(self, port):
        try:
            s = SerialSubscriber()
            serial_port = self.spm.SerialPort(port, baudrate=57600, timeout=1.5, write_timeout=0, subscriber=s)
            #start_port(port)
            serial_port.write_to_serial('v')
            p = Process(target=serial_port.packets_stream)
            print("Starting process")
            p.start()
            self.ports[port] = serial_port  
            self.process_ids.append(p.pid)
        except Exception as e: 
            print(f"Couldn't connect to serial port: {port}")
            print(e)
    
    def update_exercise_quantities(self, data):
        # TODO: use data to update the training quantites
        # Will most likely need to be threaded
        
        # NOTE: exercise type is either 1 for deadlifts or 2 for squats
        # Squats need the 6th data component, while deadlifts need the 4th. 
        # This can be automatically selected creating using as index: 1 + 2 * exercise_type

        tuning_data = data[:, 1 + 2 * self.exercise_type]
        tuning_packets_num = data.shape[0]
        # Extracting the signal quantities
        peaks, peaks_properties = find_peaks(tuning_data, height=0.5, width = 30)  # NOTE: was originally 40 but was too strict
        valleys, valley_properties = find_peaks(-tuning_data, height=0.5, width = 30)
        # If the algorithm detects at least one peak and a valley
        if peaks.size > 0 and valleys.size > 0:
            # Find zero-crossings
            zero_crosses = np.where(np.roll(tuning_data, -1)*tuning_data<0)[0]
            zeroc_pos2neg = zero_crosses[np.nonzero(tuning_data[zero_crosses]>0)]
            zeroc_neg2pos = zero_crosses[np.nonzero(tuning_data[zero_crosses]<0)]

            dt = 0
            threshold_percentage = 0.5
            
            for peak in peaks: 
                # Finding the peaks/zero-crossings correspondences
                crossings_pre_peak = np.where(zeroc_neg2pos < peak)[0]
                crossings_post_peak = np.where(zeroc_pos2neg > peak)[0]
                dt = dt + zeroc_pos2neg[crossings_post_peak[0]] - zeroc_neg2pos[crossings_pre_peak[-1]]

            dt = dt/len(peaks)

            # TODO: this could be a pop-up window
            print(f"Average number of samples between the start and end of the peaks: {dt}")
            print(f"Number of repetitions: {len(peaks)}")
            # Finding amplitude thresholds for findpeaks function
            heights = peaks_properties["peak_heights"]
            print('Height of all peaks:', heights)
            peak_height = np.mean(heights)
            print('Average peak height: {}'.format(peak_height))
            heights_valleys = valley_properties["peak_heights"]
            valley_height = np.mean(heights_valleys)
            print('Average valley height: {}'.format(valley_height))                    
            p_threshold_amp = round(peak_height*threshold_percentage,2)
            print(f'Peaks threshold height:{p_threshold_amp}')
            v_threshold_amp = round(valley_height*threshold_percentage,2)
            print(f'Valleys threshold height:{v_threshold_amp}')
            """
            self.initial_calibration_flag = True
            self.n_rep = 0
            elf.repetitions = [[] for i in range(2)]
            """
        else: 
            print("Please, repeat the calibration session")

    def write_file(self, path, filename):
        if len(self.ports) > 0: 
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
                for port in self.ports.keys():
                    np.savetxt(
                        f"{path}/{filename}-{port.split('/')[-1]}.csv", 
                        self.ports[port].listener.queue[1:], 
                        delimiter=',', 
                        header="Acc_x,Acc_y,Acc_z,Gyro_x,Gyro_y,Gyro_z,Mag_x,Mag_y,Mag_z, FreeAcc_x, FreeAcc_y, FreeAcc_z", 
                        comments="")

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
        else: 
            top = ttk.Toplevel()
            top.title("WARNING")
            _frame = ttk.Frame(top, padding = 25)
            _frame.pack(expand = NO, side=TOP)
            label = ttk.Label(_frame, text = "No active port to store data from.")
            label.pack(expand = NO)
            _but = ttk.Frame(top, padding = 15)
            _but.pack(expand = NO, side=TOP)
            but = ttk.Button(_but, text = 'Quit', command = top.destroy, bootstyle="outline-warning")
            but.pack(expand = NO)   
            top.transient()
            top.grab_set()


class View(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=15, bootstyle="dark")
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
        self.outer_l_column = ttk.Frame(self, bootstyle="dark")
        self.outer_l_column.pack(fill=Y, expand=NO, side=LEFT)
        #  ----------------------------------------------------------------
        # SpaceSensor labelled frame
        self.ss_frame = ttk.Frame(self.outer_l_column, bootstyle="dark", padding=10)
        self.ss_frame.pack(pady=10)
        ss_lframe_label = ttk.Label(self.ss_frame, text="Available SpaceSens sensors:", font="-size 18 -weight bold", bootstyle="inverse-dark")
        ss_lframe_label.pack(padx=10)
        # Scrollable frame
        self.scrolls_frame = ScrolledFrame(self.ss_frame, bootstyle="dark", height=225)
        self.scrolls_frame.pack(pady=15)
        # Sensors-related button 
        bl_button_frame = ttk.Frame(self.outer_l_column, padding=25, bootstyle="dark")
        bl_button_frame.pack()
        self.bl_button = ttk.Button(self.ss_frame, text="Start recording", command=self.recording_button_pressed, width=15,  bootstyle="success")
        self.bl_button.pack(fill=X, side=BOTTOM, expand=NO, pady=7)
        # Exercise choice button
        exc_choice_frame = ttk.Frame(self.outer_l_column, padding=25, bootstyle="dark")
        exc_choice_frame.pack()
        self.ex_choice_button = ttk.Menubutton(exc_choice_frame, text="Exercise type")
        self.ex_choice_button.pack(side=LEFT, padx=(0,5))
        self.ex_choice_button.menu = ttk.Menu(self.ex_choice_button)
        self.ex_choice_button["menu"] = self.ex_choice_button.menu
        self.ex_choice_button.menu.add_checkbutton(label='Squat', command = lambda value = 2, text = "Squat" : self.update_exercise_type(value, text))
        self.ex_choice_button.menu.add_checkbutton(label='Deadlift', command = lambda value = 1, text = "Deadlift" : self.update_exercise_type(value, text))
        self.tuning_monitor_button = ttk.Button(exc_choice_frame, command=self.monitor_tuning_button_pressed, padding=5, text="Acquire tuning data")
        self.tuning_monitor_button.pack(side=RIGHT)
        #  ----------------------------------------------------------------
        # File saving 
        fs_frame = ttk.Frame(self.outer_l_column, padding=15)
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
        save_button = ttk.Button(fs_frame, text = "Save", command= lambda : self.controller.save_file(self.directory.get(),self.file.get()))
        #save_button = ttk.Button(fs_frame, text = "Save", command= self.quit)
        save_button.pack()
        
        #Label container 
        labels_container = ttk.Frame(self.outer_l_column, bootstyle="dark", padding=25)
        labels_container.pack(side=BOTTOM, fill=BOTH, expand=NO)
        iss = ttk.Label(labels_container, bootstyle="inverse-dark", image='iss').pack(fill=X, side=RIGHT)
        asi = ttk.Label(labels_container, bootstyle="inverse-dark", image='asi').pack(fill=X, side=RIGHT)
        #  ----------------------------------------------------------------
        # Plots section 
        outer_r_column = ttk.Frame(self, bootstyle="dark", padding=15)
        outer_r_column.pack(fill=BOTH, expand=YES, side=TOP)
        # Exercise classification:
        exercise_label_frame = ttk.Frame(self, bootstyle="dark")
        exercise_label_frame.pack(fill=BOTH, expand=NO)

        exercise_title = ttk.Label(exercise_label_frame, text="Exercise execution classification:", bootstyle="inverse-dark", font="-size 18 -weight bold").pack(pady=5, side=TOP)
        self.classification = ttk.Label(exercise_label_frame, bootstyle="inverse-dark", text="No exercise detected", font="-size 16")
        self.classification.pack(pady=5)

        self.plot_frame = ttk.Frame(outer_r_column, padding = 25)
        self.plot_frame.pack(fill=BOTH, expand=YES)

        # Data label
        data_label = ttk.Label(self.plot_frame, text= "SpaceSens data plots:", font="-size 18 -weight bold").pack(fill=X)
        self.quit_button = ttk.Button(self.plot_frame, text = "Close tab", bootstyle="outline-danger", command= self.quit_button_pressed)
        self.quit_button.pack(side=RIGHT, padx=5)
        self.quit_button.configure(state=DISABLED)
        self.notebook = ttk.Notebook(self.plot_frame, padding=15)
        self.notebook.pack(fill=BOTH, expand=YES)

    
    def set_controller(self, controller):
        self.controller = controller
        # Once the controller is set, sensors can be inserted in the view  
        self.controller.create_sensors_list()
        
    
    def recording_button_pressed(self):
        if self.controller:
            self.controller.record()

    def monitor_tuning_button_pressed(self):
         if self.controller:
            self.controller.grab_tuning_data()
    
    def saved_button_pressed(self, directory, filename):
        if self.controller:
            self.controller.save_file(directory, filename)
    
    def quit_button_pressed(self):
        if self.controller:
            self.controller.quit()
    
    def update_exercise_type(self, value, text):
        self.ex_choice_button.configure(text=text)
        if self.controller:
            self.controller.update_exercise_type(value)
    



    