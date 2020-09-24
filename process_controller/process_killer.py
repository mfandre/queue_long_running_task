from multiprocessing import Process, Pipe, Queue, Pool
import os
import sys
import psutil
import signal

class ProcessKiller:
    __PID = None    

    def __init__(self, pid):
        self.__PID = pid

    def kill(self):
        try:
            print("killing", self.__PID)
            parent = psutil.Process(self.__PID)
            print("current",parent)
            children = parent.children(recursive=True)
            print("childrens", children)

            #kill children
            for process in children:
            #    if not (process.pid == PID):
                print("Process: ",self.__PID,  " killed process: ", process.pid)
                process.send_signal(signal.SIGTERM)
            
            #kill parent
            parent.send_signal(signal.SIGTERM)
        except psutil.NoSuchProcess:
            print("This PID doesnt exists")

if __name__ == '__main__':
    while(True):
        pid = None
        try:
            pid=int(input('PID (0 to exit):'))
            if pid == 0:
                try:
                    sys.exit(0)
                except SystemExit:
                    os._exit(0)
            pk = ProcessKiller(pid)
            pk.kill()
        except ValueError:
            print("Not a number")
            continue 
    