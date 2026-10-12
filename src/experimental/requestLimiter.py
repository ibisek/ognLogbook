import flask
from functools import wraps
from flask import request
from redis import StrictRedis

from configuration import redisConfig, REDIS_RECORD_EXPIRATION


class RequestLimiter:

    def __init__(self):
        self.redis = StrictRedis(**redisConfig)

    def _saveToRedis(self, key: str, value, expire=REDIS_RECORD_EXPIRATION):
        self.redis.set(key, str(value))
        self.redis.expire(key, expire)

    def _getFromRedis(self, key, default=None):
        res = self.redis.get(key)
        if not res:
            return default
        else:
            return res.decode('utf-8')

    def _putOnBlacklist(self):
        key = f"BL_{request.remote_addr}"
        self.redis.set(key, True)
        self.redis.expire(key, REDIS_RECORD_EXPIRATION)

    def _isOnBlacklist(self):
        key = f"BL_{request.remote_addr}"
        res = self._getFromRedis(key, default=False)
        return res

    def limit(self, maxLimit=0):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if request.cookies.get('bot', None) != 'false':
                    self._putOnBlacklist()
                    return flask.render_template('error40x.html', code=404, message="Not found :P"), 404

                if self._isOnBlacklist():
                    return flask.render_template('error40x.html', code=404, message="Not found :P"), 404

                if maxLimit > 0:
                    key = f"DL_{request.remote_addr}"
                    numHits = self.redis.incrby(key, 1)
                    if numHits >= 1:
                        self.redis.expire(key, REDIS_RECORD_EXPIRATION)
                    if numHits > maxLimit:
                        return flask.render_template('error40x.html', code=404, message="Nope :P"), 404

                return f(*args, **kwargs)   # call the actual annotated function
            return decorated_function
        return decorator
