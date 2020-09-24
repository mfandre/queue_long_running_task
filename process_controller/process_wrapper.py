from multiprocessing import Process, Pipe, Queue, Pool
from os import getpid
import psutil

class ProcessWrapper:
    __callable = None
    mainProcessPID = None
    childProcessPID = None
    __process = None
    __q = None

    def __init__(self, callable):
        self.__callable = callable

    def execute(self, *args):
        #creating my list of parameters
        #self.__q = Queue() #to get the return
        #f_args = args + (self.__q,)

        self.__process = Process(target=self.__callable, args=args)
        self.__process.start()

        self.mainProcessPID = self.__process.pid #getpid()
        #print("main PID",self.mainProcessPID)

        #parent = psutil.Process(self.mainProcessPID)
        #children = parent.children(recursive=True)
        #print("childrens", children)
        #self.childProcessPID = children
    
    def join(self):
        self.__process.join()

#test functions...
def long_running():
    PID = getpid()
    print("long_running", PID)
    for i in range(1,200000000):
        pass
    print("end long_running",getpid())
    result = True
    print(result)
    return result

def sum(a, b):
    PID = getpid()
    print("sum", PID)
    result = a + b
    print(result)
    return result

if __name__ == '__main__':
    pw = ProcessWrapper(long_running)
    pw.execute()
    pw.join()

    pw2 = ProcessWrapper(sum)
    pw2.execute(1,2)
    pw2.join()
    
    #print("main",getpid())
    #p = Process(target=sum, args=(1,2))
    #p = Process(target=long_running)
    #p.start()
    #p.join()
    #print(p)