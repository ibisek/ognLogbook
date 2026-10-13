import flask
from functools import wraps
from flask import request
from redis import StrictRedis

from configuration import redisConfig, REDIS_RECORD_EXPIRATION


class RequestLimiter:
    UA_BLACK_LIST = [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36',
    ]

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
        self.redis.set(key, 1)
        self.redis.expire(key, REDIS_RECORD_EXPIRATION)

    def _isOnBlacklist(self):
        key = f"BL_{request.remote_addr}"
        res = self._getFromRedis(key, default=False)
        return True if res == '1' else False

    def limit(self, maxLimit=0, blackListLimit=666):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # 1. the cookie should be correctly set by now!
                if request.path == '/set_timezone' and request.cookies.get('bot', True) != 'false':
                    self._putOnBlacklist()
                    return flask.render_template('error40x.html', code=404, message='Not found.'), 404

                # 2. if identified as bot
                # 3. the UA from the BL
                if request.cookies.get('bot', None) == 'true' \
                        or request.headers.get('User-Agent', None) in self.UA_BLACK_LIST:
                    self._putOnBlacklist()
                    return flask.render_template('error40x.html', code=404, message='Not found.'), 404

                if request.cookies.get('bot', None) == 'true':
                    self._putOnBlacklist()
                    return flask.render_template('error40x.html', code=404, message='Not found.'), 404

                if self._isOnBlacklist():
                    return flask.render_template('error40x.html', code=404, message='Not found.'), 404

                if maxLimit > 0:
                    key = f"DL_{request.remote_addr}"
                    numHits = self.redis.incrby(key, 1)

                    if numHits >= 1:
                        self.redis.expire(key, REDIS_RECORD_EXPIRATION)

                    if numHits > blackListLimit:
                        self._putOnBlacklist()

                    if numHits > maxLimit:
                        return flask.render_template('error40x.html', code=404, message="Nope :P"), 404

                return f(*args, **kwargs)   # call the actual annotated function
            return decorated_function
        return decorator
