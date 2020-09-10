"""
General periodic tasks are defined and executed from here.
"""

from periodicTimer import PeriodicTimer
from cron.towLookup import TowLookup
from cron.redisReaper import RedisReaper


class CronJobs(object):
    def __init__(self):
        tl = TowLookup()
        self.towLookupTimer = PeriodicTimer(TowLookup.INTERVAL, tl.gliderTowLookup)
        self.towLookupTimer.start()

        # self.rr = RedisReaper()
        # self.redisReaperTimer = PeriodicTimer(RedisReaper.INTERVAL, self.doWork())

    def stop(self):
        self.towLookupTimer.stop()

        # self.redisReaperTimer.stop()
        # self.rr.stop()

        print("[INFO] Cron terminated.")
