

# NOTE: solo di prova!!

import logging
import time
import threading
from threading import Thread
from _serial import SerialPortManager, SerialPort

spm = SerialPortManager()
ports = spm.load_ports()


class Threading_():

    def thread_function(ports,index):
        # trasmetto un thread per volta
        logging.info("Thread %s: starting", ports[index])
        t = SerialPort.start_stream()
        time.sleep(1.5)
        logging.info("Thread %s: finishing", ports[index])


    if __name__ == "__main__":

        threads = list()
        for index in enumerate(ports):
            format = "%(asctime)s: %(message)s"
            logging.basicConfig(format = format, level = logging.INFO, datefmt = "%H:%M:%S")
            logging.info("Create thread %d.", index)
            x = Thread(target=thread_function, args=(index,))
            threads.append(x)
            x.start()


        for index, thread in enumerate(threads):
            # unifico tutti i thread
            thread.join()
            logging.info("Thread %d done", ports[index])