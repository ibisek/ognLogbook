"""
General periodic tasks are defined and executed from here.
"""

from periodicTimer import PeriodicTimer
from cron.towLookup import TowLookup


class CronJobs(object):
    def __init__(self):
        tl = TowLookup()
        self.towLookup = PeriodicTimer(TowLookup.INTERVAL, tl.gliderTowLookup)
        self.towLookup.start()

    def stop(self):
        self.towLookup.stop()
        print("[INFO] Cron terminated.")
