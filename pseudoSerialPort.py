#!/usr/bin/env python3

import os, pty, serial
import time, sys

if __name__=='__main__':

    master,slave = pty.openpty()  # open the pseudoterminal
    s_name = os.ttyname(slave)    # translate the slave fd to a filename
    print("Connect to: \033[1;33m{}\033[0m".format(s_name))

    s = input("Press any key to start...")
    print("\033[1;32m [INFO]\033[0m Simulating the serial port...")

    counter = 0
    TxBuffer = bytearray(9)
    TxBuffer[0]  = 0xA0
    TxBuffer[-1] = 0xC0
    gsrValue = 512
    TxBuffer[5:7] = gsrValue.to_bytes(2, sys.byteorder)
    
    while 1:
        counter = counter+1
        TxBuffer[1:5] = counter.to_bytes(4, sys.byteorder)
        os.write(master, TxBuffer)
        time.sleep(0.02)
