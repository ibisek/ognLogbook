"""
Redis-like dict with configurable expiration.

@author ibisek
@version 2021-09-09
"""

from time import time


class ExpiringDict(dict):

    def __init__(self, ttl: int, *args):
        """
        :param ttl: time-to-live [s]
        :param args:
        """
        dict.__init__(self, args)
        self.ttl = ttl
        self.lastTickTs = 0

    def __getitem__(self, key):
        return dict.__getitem__(self, key)[0]

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, (val, time()))

    def tick(self):
        """
        This needs to be called periodically from <somewhere> to drop expired records.
        """

        now = time()

        if now - self.lastTickTs < self.ttl:
            return
        self.lastTickTs = now

        keys = [key for key in self.keys()]     # we are about to drop some keys - hence this pre-caching
        for key in keys:
            ts = dict.__getitem__(self, key)[1]
            if now - ts > self.ttl:
                del self[key]


if __name__ == '__main__':
    d = ExpiringDict(ttl=3)
    d["aaa"] = 111
    d["bbb"] = 222

    d.tick()
    print("1:", d)

    from time import sleep
    sleep(4)
    d.tick()
    print("2:", d)
