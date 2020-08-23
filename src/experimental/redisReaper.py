"""
(1) Find "orphaned" records in redis (with last status update >= 30 min),
(2) Check last known status of the aircraft from influx,
(3) if dAlt < 0 (descending) and alt < 100m and near to an airfield create landing event,
(4) mark as landed in redis.
"""

from redis import StrictRedis

from configuration import redisConfig

redis = StrictRedis(**redisConfig)

if __name__ == '__main__':

    keys = redis.keys('*status')
    for key in keys:
        ttl = redis.ttl(key)
        print(f'{key} -> {ttl}')

        # TODO last position data from influx
        # TODO klesal a byl < 100m AGL -> pristani
        # TODO nastavit v redisu jako on-ground/landed nebo smazat

    pass
