"""
Event Watcher to inform retistered users about airplane events (take-off/landing)
"""

from datetime import datetime
from redis import StrictRedis

from configuration import dbConnectionInfo, redisConfig, ADDRESS_TYPE_PREFIX, ADDRESS_TYPES
from cron.eventWatcher.sendMail3 import SendMail3
from db.DbSource import DbSource
from cron.eventWatcher.messageFormatter import formatMailNotification


class WatcherEvent:
    __slots__ = ('ts', 'event', 'address', 'addressType', 'lat', 'lon', 'icaoLocation', 'flightTime')

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
    __slots__ = ('userId', 'email', 'lang', 'aircraft_registration', 'aircraft_cn')

    def __init__(self, row):
        self.userId, self.email, self.lang, self.aircraft_registration, self.aircraft_cn = row
        self.userId = int(self.userId)


class EventWatcher:
    REDIS_KEY = 'watcher_events'
    RUN_INTERVAL = 10  # [s]

    busy = False

    def __init__(self):
        self.redis = self.redis = StrictRedis(**redisConfig)

    @staticmethod
    def createEvent(redis,
                    ts: int, event: str, address: str, addressType: int,
                    lat: float, lon: float, icaoLocation: str, flightTime: int):
        rec = f"{ts};{event};{address};{addressType};{lat:.5f};{lon:.5f};{icaoLocation};{flightTime}"
        redis.rpush(EventWatcher.REDIS_KEY, rec)

    @staticmethod
    def _listWatchers(addressType: int, address: str, eventType: str):
        addressTypeChar: str = ADDRESS_TYPES[addressType]
        eventCond = 'AND w.w_land IS true' if eventType == 'L' else 'AND w.w_toff IS true'
        dayCond = f"AND w.w_{datetime.now().strftime('%a').lower()} IS true"

        strSql = f"SELECT u.id, u.email, u.lang, d.aircraft_registration, a.aircraft_cn FROM watchers AS w " \
                 f"LEFT JOIN users AS u ON u.id = w.user_id " \
                 f"LEFT JOIN airplanes AS a ON a.device_id = w.addr AND a.device_type = w.addr_type " \
                 f"WHERE addr_type = '{addressTypeChar}' AND addr = '{address}' " \
                 f"{eventCond} {dayCond};"

        watchers = []
        with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
            cur.execute(strSql)
            for row in cur:
                w = Watcher(row)
                watchers.append(w)

        return watchers

    @staticmethod
    def _notifyWatcher(watcher: Watcher, event: WatcherEvent):
        if event.icaoLocation:
            dt = datetime.fromtimestamp(event.ts).isoformat()
            print(f"[INFO] Watcher notif. [{event.ts} | {dt}] <{event.event}> @ {event.icaoLocation} {watcher.aircraft_registration} ({watcher.aircraft_cn}) to {watcher.email}")

            subject, body = formatMailNotification(event, watcher)
            try:
                SendMail3().sendMail(receiver_email=watcher.email, subject=subject, text=body)
            except Exception as e:
                print("[ERROR] Email not sent due to ", e)
                # TODO asi by to chtelo ulozit zpravu pro pozdejsi odeslani..

    def processEvents(self):
        if self.busy:
            return  # never execute another process when the previous is still running
        self.busy = True

        # while rec := self.redis.lpop(EventWatcher.REDIS_KEY):
        while self.redis.llen(EventWatcher.REDIS_KEY) > 0:
            rec = self.redis.lpop(EventWatcher.REDIS_KEY)
            if not rec:
                break

            event = WatcherEvent(rec)
            watchers = self._listWatchers(addressType=event.addressType, address=event.address, eventType=event.event)

            for watcher in watchers:
                # if watcher.startTs and watcher.startTs > now():
                #     continue # TODO not yet active watcher

                self._notifyWatcher(watcher, event)

                # if watcher.expirationTs < now():
                #     # TODO delete the watcher

        self.busy = False


if __name__ == '__main__':
    redis = StrictRedis(**redisConfig)

    # EventWatcher.createEvent(redis=redis,
    #                          ts=int(datetime.now().timestamp()), event='L', address='C35001', addressType=3,
    #                          lat=49.123, lon=16.123, icaoLocation='LKKA', flightTime=666)

    ev = EventWatcher()

    while True:
        ev.processEvents()
