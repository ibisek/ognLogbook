"""
Event Watcher to inform retistered users about airplane events (take-off/landing)
"""

from redis import StrictRedis

from configuration import redisConfig, ADDRESS_TYPE_PREFIX


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

    def processEvents(self):
        numRecs = self.redis.llen(EventWatcher.REDIS_KEY)
        if numRecs == 0:
            return

        while rec := self.redis.lpop(EventWatcher.REDIS_KEY):
            ts, event, address, addressType, lat, lon, icaoLocation, flightTime = rec.decode('utf-8').split(';')
            addrPrefix = ADDRESS_TYPE_PREFIX[int(addressType)]

            # TODO list watchers:
            strSql = f"SELECT * FROM watchers WHERE address = '{addrPrefix}{address}';"
            print("strSql:", strSql)

            # TODO notify watchers:


if __name__ == '__main__':
    redis = StrictRedis(**redisConfig)
    EventWatcher.createEvent(redis=redis,
                             ts=1, event='X', address='123456', addressType=0,
                             lat=49.123, lon=16.123, icaoLocation='LKKA', flightTime=666)

    ev = EventWatcher()
    ev.processEvents()
