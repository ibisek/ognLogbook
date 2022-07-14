"""
Event Watcher to inform retistered users about airplane events (take-off/landing)
"""

from datetime import datetime
from redis import StrictRedis

from configuration import dbConnectionInfo, redisConfig, ADDRESS_TYPE_PREFIX, ADDRESS_TYPES
from cron.sendMail3 import SendMail3
from db.DbSource import DbSource
from utils import formatDuration


class WatcherEvent:
    def __init__(self, line):
        self.ts, self.event, self.address, self.addressType, self.lat, self.lon, self.icaoLocation, self.flightTime = line.decode('utf-8').split(';')

        self.ts = int(self.ts)
        self.addressType = int(self.addressType)
        self.lat = float(self.lat)
        self.lon = float(self.lon)
        self.flightTime = int(self.flightTime) if self.flightTime else 0

    @property
    def addressWithPrefix(self):
        addrPrefix = ADDRESS_TYPE_PREFIX[int(self.addressType)]
        return f"{addrPrefix}{self.address}"


class Watcher:
    def __init__(self, row):
        self.userId, self.email, self.lang, self.aircraft_registration, self.aircraft_cn = row
        self.userId = int(self.userId)


class EventWatcher:
    REDIS_KEY = 'watcher_events'
    RUN_INTERVAL = 10  # [s]

    def __init__(self):
        self.redis = self.redis = StrictRedis(**redisConfig)

    @staticmethod
    def createEvent(redis,
                    ts: int, event: str, address: str, addressType: int,
                    lat: float, lon: float, icaoLocation: str, flightTime: int):
        rec = f"{ts};{event};{address};{addressType};{lat:.5f};{lon:.5f};{icaoLocation};{flightTime}"
        redis.rpush(EventWatcher.REDIS_KEY, rec)

    def _listWatchers(self, addressType: int, address: str):
        addressTypeChar: str = ADDRESS_TYPES[addressType]
        strSql = f"SELECT u.id, u.email, u.lang, d.aircraft_registration, d.aircraft_cn FROM watchers AS w " \
                 f"LEFT JOIN users AS u ON u.id = w.user_id " \
                 f"LEFT JOIN ddb AS d ON d.device_id = w.addr AND d.device_type = w.addr_type " \
                 f"WHERE addr_type = '{addressTypeChar}' AND addr = '{address}';"

        watchers = []
        with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
            cur.execute(strSql)
            for row in cur:
                w = Watcher(row)
                watchers.append(w)

        return watchers

    def _notifyWatcher(self, watcher: Watcher, event: WatcherEvent):
        if event.icaoLocation:
            print(f"[TEMP] WATCHER [{event.ts}] <{event.event}> @ {event.icaoLocation} {watcher.aircraft_registration} ({watcher.aircraft_cn})")

            dt = datetime.fromtimestamp(event.ts)
            dt = datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")

            subject = f"{watcher.aircraft_registration} ({watcher.aircraft_cn}) @ {event.icaoLocation}"

            text = f"dt: {dt}\nevent: {event.event}"
            if event.flightTime > 0:
                text += f"\nflightTime: {formatDuration(event.flightTime)}"
            text += f"\n\nEvent location:\n\tlat: {event.lat:.4f}\n\tlon: {event.lon:.4f}"

            SendMail3().sendMail(receiver_email=watcher.email, subject=subject, text=text)

    def processEvents(self):
        pass
        numRecs = self.redis.llen(EventWatcher.REDIS_KEY)
        if numRecs == 0:
            return

        # while rec := self.redis.lpop(EventWatcher.REDIS_KEY):
        while True:
            rec = self.redis.lpop(EventWatcher.REDIS_KEY)
            if not rec:
                break

            event = WatcherEvent(rec)
            watchers = self._listWatchers(event.addressType, event.address)

            for watcher in watchers:
                self._notifyWatcher(watcher, event)


if __name__ == '__main__':
    redis = StrictRedis(**redisConfig)
    EventWatcher.createEvent(redis=redis,
                             ts=int(datetime.now().timestamp()), event='L', address='C35001', addressType=3,
                             lat=49.123, lon=16.123, icaoLocation='LKKA', flightTime=666)

    ev = EventWatcher()
    ev.processEvents()
