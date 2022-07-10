"""
Event Watcher to inform retistered users about airplane events (take-off/landing)
"""

from datetime import datetime
from redis import StrictRedis

from configuration import dbConnectionInfo, redisConfig, ADDRESS_TYPE_PREFIX, ADDRESS_TYPES
from db.DbSource import DbSource


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
            print(f"[INFO] WATCHER [{event.ts}] <{event.event}> @ {event.icaoLocation} {watcher.aircraft_registration} ({watcher.aircraft_cn})")

        # TODO poslat mail

    def processEvents(self):
        numRecs = self.redis.llen(EventWatcher.REDIS_KEY)
        if numRecs == 0:
            return

        while rec := self.redis.lpop(EventWatcher.REDIS_KEY):
            event = WatcherEvent(rec)
            watchers = self._listWatchers(event.addressType, event.address)

            for watcher in watchers:
                self._notifyWatcher(watcher, event)


if __name__ == '__main__':
    redis = StrictRedis(**redisConfig)
    EventWatcher.createEvent(redis=redis,
                             ts=int(datetime.now().timestamp()), event='?', address='C35001', addressType=3,
                             lat=49.123, lon=16.123, icaoLocation='LKKA', flightTime=666)

    ev = EventWatcher()
    ev.processEvents()
