import logging
from time import sleep
from threading import Thread


class PeriodicTimer(Thread):

    __slots__ = ('interval', 'function', 'doRun')

    def __init__(self, interval, function):
        """
        :param interval: [s]
        :param function: function handle to call in intervals
        """
        super(PeriodicTimer, self).__init__()

        self.interval = interval
        self.function = function

        self.doRun = True

    def run(self):
        while self.doRun:
            for i in range(self.interval):
                sleep(1)  # ~ thread.yield()
                if not self.doRun:
                    break

            if self.doRun:
                try:
                    self.function()
                except Exception as e:
                    logging.error("A cron job excepted with:", str(e))

    def stop(self):
        self.doRun = False
