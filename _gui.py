from matplotlib.pyplot import axhline
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
        print(f"Calibrating {port}")
        ports = self.model.ports
        # Clear the queue before calibration
        ports[port].clear_queue()
        # Send calibration signal to Arduino
        ports[port].write_to_serial('b')
        # Starts collecting the calibration data on the listener
        ports[port].start_recording()
        # Waits for magetometer data to be collected and stop collection
        time.sleep(10)
        ports[port].stop_recording()
        # Ask model to process data
        uncalibrated_data, calibrated_data = self.model.process_calibration_data(port)
        self.view.display_calibration_outcomes(uncalibrated_data, calibrated_data)

    def perform_tuning(self):
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
                    message = "Add corresponding sensor for tuning: right thigh for squats, pelvis for deadlift"
                    self.view.display_warning_popup(message)
            elif self.tuning:
                self.view.tuning_monitor_button.configure(bootstyle='primary')
                self.view.tuning_monitor_button.configure(text='Acquire tuning data')
                self.tuning = False
                ports[exercise_ports[exercise_type]].stop_recording()
                tuning_outcomes = self.model.analyze_exercise_tuning_data(ports[exercise_ports[exercise_type]].listener.queue[1:])
                if len(tuning_outcomes) > 0:
                    self.view.display_tuning_outcomes(tuning_outcomes)
                else: self.view.display_warning_popup("Calibration sesssion must be repeated!")

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
        outcome = self.model.write_file(path, filename)
        self.view.display_saving_outcome(outcome)

    def quit(self):
        nb = self.view.notebook
        #def deletetab():
        for item in nb.winfo_children():
            if str(item) == (nb.select()):
                #print(nb.select())
                item.destroy()
                return  #Necessary to break or for loop can destroy all the tabs when first tab is deleted


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
        pass

    def analyze_exercise_tuning_data(self,data):
        analysis_outcomes = {}  # Initializing the outcomes to be sent to View for display
        dt = 0
        threshold_percentage = 0.5 # Will be used to set the threshold values
        # NOTE: exercise type is either 1 for deadlifts or 2 for squats
        # Squats need the 6th data component, while deadlifts need the 4th. 
        # This can be automatically selected creating using as index: 1 + 2 * exercise_type
        tuning_data = data[:, 1 + 2 * self.exercise_type]
        #tuning_packets_num = data.shape[0]
        # Extracting the signal quantities
        peaks, peaks_properties = find_peaks(tuning_data, height=0.5, width = 30)  # NOTE: was originally 40 but was too strict
        valleys, valleys_properties = find_peaks(-tuning_data, height=0.5, width = 30)
        
        # If the algorithm detects at least one peak and a valley
        if peaks.size > 0 and valleys.size > 0:
            # Find zero-crossings
            zero_crosses = np.where(np.roll(tuning_data, -1)*tuning_data<0)[0]
            zeroc_pos2neg = zero_crosses[np.nonzero(tuning_data[zero_crosses]>0)]
            zeroc_neg2pos = zero_crosses[np.nonzero(tuning_data[zero_crosses]<0)]
            for peak in peaks: 
                # Finding the peaks/zero-crossings correspondences
                crossings_pre_peak = np.where(zeroc_neg2pos < peak)[0]
                crossings_post_peak = np.where(zeroc_pos2neg > peak)[0]
                dt = dt + zeroc_pos2neg[crossings_post_peak[0]] - zeroc_neg2pos[crossings_pre_peak[-1]]
            dt = dt/len(peaks)

            # Packing the results in their dictionary
            analysis_outcomes["data"] = tuning_data
            analysis_outcomes["rising_crossings_timestamps"] = zeroc_neg2pos
            analysis_outcomes["falling_crossings_timestamps"] = zeroc_pos2neg
            analysis_outcomes["dt"] = dt
            analysis_outcomes["num"] = len(peaks)
            analysis_outcomes["peaks_timestamps"] = peaks
            analysis_outcomes["valleys_timestamps"] = valleys
            peaks_heights = peaks_properties["peak_heights"]
            analysis_outcomes["p_heights"] = peaks_heights
            peak_height = np.mean(peaks_heights)
            analysis_outcomes["avg_p_height"] = peak_height
            valley_depths = valleys_properties["peak_heights"]
            analysis_outcomes["v_depths"] = valley_depths
            valley_depth = np.mean(valley_depths)
            analysis_outcomes["avg_v_depth"] = valley_depth
            analysis_outcomes["p_threshold"] = round(peak_height*threshold_percentage,2)
            analysis_outcomes["v_threshold"] = round(valley_depth*threshold_percentage,2)
            
        return analysis_outcomes
    
    def process_calibration_data(self, port):
        uncalibrated_data = self.ports[port].listener.queue[1:,6:9]
        # Extracting min-max values
        min_mag_cal_data = np.min(uncalibrated_data, axis=0)
        max_mag_cal_data = np.max(uncalibrated_data, axis=0)
        # Computing the average
        mag_bias = np.round((np.mean((min_mag_cal_data, max_mag_cal_data), axis=0)),2)
        # Computing the element-wise difference and its mean
        mag_diff = (max_mag_cal_data - min_mag_cal_data)/2
        mag_mean = np.sum(mag_diff)/3
        # Packing data 
        mag_scale = np.round((1/mag_diff * mag_mean),2)
        data_str = f"{mag_bias[0]},{mag_scale[0]},{mag_bias[1]},{mag_scale[1]},{mag_bias[2]},{mag_scale[2]}\n"
        print(data_str)
        # Send calibration quantities back to Arduino
        self.ports[port].write_to_serial(data_str)
        calibrated_data = np.multiply((uncalibrated_data - mag_bias), mag_scale) 
        return uncalibrated_data, calibrated_data

    def write_file(self, path, filename):
        # Writes the file and returns a value corresponding to the error (if any) 
        # 1: fields not filled
        # 2: no directory found
        # 3: saving exception
        # 4: no serial available / no data
        msg = 0  # Everything goes well 

        if len(self.ports) > 0: 
            if not path or not filename:
                msg = 1
            elif not os.path.isdir(path): 
                msg = 2
            else: 
                try:
                    for port in self.ports.keys():
                        np.savetxt(
                            f"{path}/{filename}-{port.split('/')[-1]}.csv", 
                            self.ports[port].listener.queue[1:], 
                            delimiter=',', 
                            header="Acc_x,Acc_y,Acc_z,Gyro_x,Gyro_y,Gyro_z,Mag_x,Mag_y,Mag_z, FreeAcc_x, FreeAcc_y, FreeAcc_z", 
                            comments="")
                except: msg = 3
        else: 
            msg = 4
        
        return msg


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
        self.ex_choice_button.menu.add_checkbutton(label='Squat', command = lambda value = 2, text = "Squat" : self.exercise_type_selected(value, text))
        self.ex_choice_button.menu.add_checkbutton(label='Deadlift', command = lambda value = 1, text = "Deadlift" : self.exercise_type_selected(value, text))
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
            self.controller.perform_tuning()
    
    def saved_button_pressed(self, directory, filename):
        if self.controller:
            self.controller.save_file(directory, filename)
    
    def quit_button_pressed(self):
        if self.controller:
            self.controller.quit()
    
    def exercise_type_selected(self, value, text):
        self.ex_choice_button.configure(text=text)
        if self.controller:
            self.controller.update_exercise_type(value)
    
    def display_warning_popup(self, message):
        top = ttk.Toplevel()
        top.title('Warning')
        _frame = ttk.Frame(top, padding = 25)
        _frame.pack(expand = NO, side=TOP)
        label = ttk.Label(_frame, text = message)
        label.pack(expand = NO)
        _but = ttk.Frame(top, padding = 15)
        _but.pack(expand = NO, side=TOP)
        but = ttk.Button(_but, text = 'Okay', command = top.destroy, bootstyle="outline-warning")
        but.pack(expand = NO)   
        top.transient()
        top.grab_set()

    def display_saving_outcome(self, outcome):
        _error_messages = {
            1: "Please, fill the required fields!", 
            2: "Directory not found!",
            3: "Saving exception, please make sure data has been read from sensors",
            4: "No active port to store data from!"
        }
        if outcome == 0:
            # Pop-up success window
            top = ttk.Toplevel()
            top.title('File(s) correctly saved')
            _frame = ttk.Frame(top, padding = 25)
            _frame.pack(expand = NO, side=TOP)
            label = ttk.Label(_frame, text = f"Data saved in {self.directory.get()}/{self.file.get()}-*.csv", \
                                            wraplength=220, anchor=ttk.NW, justify=ttk.LEFT)
            label.pack(expand = NO)
            _but = ttk.Frame(top, padding = 15)
            _but.pack(expand = NO, side=TOP)
            but = ttk.Button(_but, text = 'Okay', command = top.destroy, bootstyle = "outline-success")
            but.pack(expand = NO)   
            top.transient()
            top.grab_set()
        else:
            # Pop-up warning window
            top = ttk.Toplevel()
            top.title('Warning')
            _frame = ttk.Frame(top, padding = 25)
            _frame.pack(expand = NO, side=TOP)
            label = ttk.Label(_frame, text = _error_messages[outcome])
            label.pack(expand = NO)
            _but = ttk.Frame(top, padding = 15)
            _but.pack(expand = NO, side=TOP)
            but = ttk.Button(_but, text = 'Okay', command = top.destroy, bootstyle="outline-warning")
            but.pack(expand = NO)   
            top.transient()
            top.grab_set()
    
    def display_tuning_outcomes(self, analysis_outcomes):
        # Pop-up window
        top = ttk.Toplevel()
        top.title('Tuning outcomes')
        _frame = ttk.Frame(top, padding = 25)
        _frame.pack(fill=BOTH, expand=NO)
        # Creating the figure and the corresponding tkinter widget
        figure = Figure(figsize=(16, 8), dpi=100)
        figure.patch.set_facecolor('#222222')
        figure_canvas = FigureCanvasTkAgg(figure, _frame)
        figure_canvas.get_tk_widget().pack(fill=BOTH,  expand=YES, side=TOP)
        # Setting plot colors and quantities 
        _grey_rgb = (197/255, 202/255, 208/255)
        _font = {   'family': 'sans-serif',
                    'color':  'white',
                    'weight': 'normal',
                    'size': 14,
            }
        # Create the axis
        ax = figure.add_subplot()
        ax.set_facecolor('#222222')
        ax.tick_params(color=_grey_rgb, labelcolor=_grey_rgb)
        for spine in ax.spines.values():
            spine.set_edgecolor(_grey_rgb)
        # Unpacking the outcomes dictionary
        tuning_data = analysis_outcomes["data"] 
        zeroc_neg2pos = analysis_outcomes["rising_crossings_timestamps"]
        zeroc_pos2neg = analysis_outcomes["falling_crossings_timestamps"]
        p_threshold_amp = analysis_outcomes["p_threshold"]
        v_threshold_amp = analysis_outcomes["v_threshold"]
        peaks = analysis_outcomes["peaks_timestamps"]
        valleys = analysis_outcomes["valleys_timestamps"]
        # Preparing the figure
        ax.set_ylabel("Tuning data", fontdict=_font)
        ax.set_xlabel("Number of samples", fontdict=_font)
        ax.plot(range(len(tuning_data)), tuning_data, color="#ffffff")
        ax.plot(range(len(tuning_data)), np.zeros(tuning_data.shape, dtype="int8"), linestyle="dashed", color="#c5cad0")
        ax.plot(range(len(tuning_data)), np.repeat([p_threshold_amp], len(tuning_data)), label="Peaks threshold", color='#299CB1')
        ax.plot(range(len(tuning_data)), np.repeat([-v_threshold_amp], len(tuning_data)), label="Valleys threshold", color='#18B179')
        #ax.scatter(x=zeroc_pos2neg,y=tuning_data[zeroc_pos2neg], c='r')
        #ax.scatter(x=zeroc_neg2pos,y=tuning_data[zeroc_neg2pos], c='g')
        ax.scatter(x=peaks,y=tuning_data[peaks], marker='o', color='#299CB1')
        ax.scatter(x=valleys,y=tuning_data[valleys], marker='s', color='#18B179')
        ax.legend(loc='upper right')
        # Drawing the final figure
        figure_canvas.draw()

         
        top.transient()
        top.grab_set()
    
    def display_calibration_outcomes(self, uncalibrated_data, calibrated_data):
        # Pop-up  window
        top = ttk.Toplevel()
        top.title('Calibration outcomes')
        _frame = ttk.Frame(top, padding = 25)
        _frame.pack(fill=BOTH, expand=NO)
        # Creating the figure and the corresponding tkinter widget
        figure = Figure(figsize=(16, 8), dpi=100)
        figure.patch.set_facecolor('#222222')
        figure_canvas = FigureCanvasTkAgg(figure, _frame)
        figure_canvas.get_tk_widget().pack(fill=BOTH,  expand=YES, side=TOP)
        # Setting plot colors and quantities 
        _grey_rgb = (197/255, 202/255, 208/255)
        _font = {   'family': 'sans-serif',
                    'color':  'white',
                    'weight': 'normal',
                    'size': 14,
            }
        # Create the subplots
        # Uncalibrated results
        uncal_ax = figure.add_subplot(121)
        uncal_ax.set_facecolor('#222222')
        uncal_ax.tick_params(color=_grey_rgb, labelcolor=_grey_rgb)
        for spine in uncal_ax.spines.values():
            spine.set_edgecolor(_grey_rgb)
        # Preparing the figure
        uncal_ax.set_title('Magnetometer AK8963 uncalibrated results', fontdict=_font)
        # Scatterpoints
        uncal_ax.scatter(x=uncalibrated_data[:,0],y=uncalibrated_data[:,1], marker='^', c="#299CB1", label='Mxy')
        uncal_ax.scatter(x=uncalibrated_data[:,0],y=uncalibrated_data[:,2], marker='s', c='#18B179', label='Mxz')
        uncal_ax.scatter(x=uncalibrated_data[:,1],y=uncalibrated_data[:,2], marker='o', c='#825194', label='Myz')
        uncal_ax.legend(loc='upper right')

        # Calibrated results
        cal_ax = figure.add_subplot(122)
        cal_ax.set_facecolor('#222222')
        cal_ax.tick_params(color=_grey_rgb, labelcolor=_grey_rgb)
        for spine in cal_ax.spines.values():
            spine.set_edgecolor(_grey_rgb)
        # Preparing the figure
        cal_ax.set_title('Magnetometer AK8963 calibrated results', fontdict=_font)
        # Scatterpoints
        cal_ax.scatter(x=calibrated_data[:,0],y=calibrated_data[:,1], marker='^', c="#299CB1", label='Mxy')
        cal_ax.scatter(x=calibrated_data[:,0],y=calibrated_data[:,2], marker='s', c='#18B179', label='Mxz')
        cal_ax.scatter(x=calibrated_data[:,1],y=calibrated_data[:,2], marker='o', c='#825194', label='Myz')
        cal_ax.legend(loc='upper right')
        
        # Drawing the final figure
        figure_canvas.draw()

        top.transient()
        top.grab_set()
        

    