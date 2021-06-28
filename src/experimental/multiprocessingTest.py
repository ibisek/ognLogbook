#!/usr/bin/python3

import time
from time import sleep
import threading
import multiprocessing as mp
import random
from queue import Empty


class Test:

    def __init__(self, id: int, queue: mp.Queue):
        self.id = id
        self.queue = queue

        self.doRun = True

    @staticmethod
    def t(idx, note):
        i = 0
        for x in range(10000000):
            i += random.randint(0, 666)
        # with open('/dev/urandom', 'rb') as f:
        # for x in range(1000):
        # f.read(4 * 65535)

    def t2(self):
        print(f"Starting id {self.id}..")
        print(f".. queue {str(self.queue)}")
        numProcessed = 0
        while self.doRun:
            interval = self.queue.get()
            print(f"[{self.id}] sleep for {interval}s")
            sleep(interval)

            newInterval = random.randint(5, 10)
            self.queue.put(newInterval)
            print(f"[{self.id}] newInterval: {newInterval}")

            numProcessed += 1
            if numProcessed > 10:
                self.doRun = False

        print(f"Id {self.id} TERMINATED")


if __name__ == '__main__':
    # queue = mp.Queue()
    queue = mp.Manager().Queue()    # this is the truly shared queue!!
    queue.put(1)
    queue.put(2)
    queue.put(3)
    queue.put(4)
    queue.put(5)
    queue.put(6)

    start_time = time.time()
    # Test().t()
    # Test().t()
    # Test().t()
    # Test().t()
    print("Sequential run time: %.2f seconds" % (time.time() - start_time))

    start_time = time.time()
    # t1 = threading.Thread(target=Test().t)
    # t2 = threading.Thread(target=Test().t)
    # t3 = threading.Thread(target=Test().t)
    # t4 = threading.Thread(target=Test().t)
    # t1 = mp.Process(target=Test().t, args=(1, "A"))
    # t2 = mp.Process(target=Test().t, args=(2, "B"))
    # t3 = mp.Process(target=Test().t, args=(3, "C"))
    # t4 = mp.Process(target=Test().t, args=(4, "D"))
    t1 = mp.Process(target=Test(1, queue).t2)
    t2 = mp.Process(target=Test(2, queue).t2)
    t3 = mp.Process(target=Test(3, queue).t2)
    t4 = mp.Process(target=Test(4, queue).t2)

    t1.start()
    t2.start()
    t3.start()
    t4.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    print("Parallel run time: %.2f seconds" % (time.time() - start_time))

    try:
        while item := queue.get_nowait():    # queue.get(block=False):
            print(f"item: {item}")
    except Empty:
        pass

    print('KOHEU.')
