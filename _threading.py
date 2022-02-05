# TODO: check multiprocessing module in Python
# Could be used to do computations on the data in parallel (e.g., filtering of the signal WHILE is being acquired)
# AVOID DATA LOSSES AT ALL COST 
from multiprocessing import Process, Pipe

class SerialReadingProcess(Process):
    def __init__(self, port):
        Process.__init__(self)
        self.port = port

    def run(self):
        self.port.my_start_stream()
    

class SerialWriterProcess(Process):
    def __init__(self, port):
        Process.__init__(self)
        self._port = port

    def run(self):
        print("Writing to serial...")
        self._port.write_stream()