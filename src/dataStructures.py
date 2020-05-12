
class Status(object):

    def __init__(self, s=-1, ts=0):
        """
        :param s: 0 = on ground, 1 = airborne, -1 = unknown
        :param ts: [s]
        """
        self.s = int(s)
        self.ts = int(ts)

    def __str__(self):
        return f"{self.s};{self.ts}"

    @staticmethod
    def parse(s):
        s = s.decode('utf-8')
        items = s.split(';')

        if len(items) != 2:
            raise ValueError(s)

        s: Status = Status(items[0], items[1])

        return s
