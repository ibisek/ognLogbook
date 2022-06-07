"""
General periodic tasks are defined and executed from here.
"""

from periodicTimer import PeriodicTimer
from cron.towLookup import TowLookup
from cron.redisReaper import RedisReaper
from cron.flownDistanceCalculator import FlownDistanceCalculator
from cron.realTakeoff import RealTakeoffLookup


class CronJobs(object):
    def __init__(self):
        tl = TowLookup()
        self.towLookupTimer = PeriodicTimer(TowLookup.RUN_INTERVAL, tl.gliderTowLookup)
        self.towLookupTimer.start()

        self.rr = RedisReaper()
        self.redisReaperTimer = PeriodicTimer(RedisReaper.RUN_INTERVAL, self.rr.doWork)
        self.redisReaperTimer.start()

        distCalc = FlownDistanceCalculator()
        self.flownDistCalcTimer = PeriodicTimer(FlownDistanceCalculator.RUN_INTERVAL, distCalc.calcDistances)
        self.flownDistCalcTimer.start()

        realTakeoffLookup = RealTakeoffLookup()
        self.realTakeoffLookupTimer = PeriodicTimer(RealTakeoffLookup.RUN_INTERVAL, realTakeoffLookup.checkTakeoffs())
        self.realTakeoffLookupTimer.start()

    def stop(self):
        self.towLookupTimer.stop()

        # self.redisReaperTimer.stop()
        # self.rr.stop()

        self.flownDistCalcTimer.stop()

        self.realTakeoffLookupTimer.stop()

        print("[INFO] Cron terminated.")
