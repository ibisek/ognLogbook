
from queue import Queue, Empty
from datetime import datetime

from configuration import dbConnectionInfo
from db.DbSource import DbSource


class TowLookup(object):
    RUN_INTERVAL = 60   # [s]
    TOW_TIME_RANGE = 4  # +/-[s]
    TOW_TIME_WINDOW = 10 * 60  # [s]

    def __init__(self):
        self.queue = Queue()
        print(f"[INFO] TowLookup scheduled to run every {self.RUN_INTERVAL}s with window "
              f"of {int(self.TOW_TIME_WINDOW/60)} min and detection range of +/- {self.TOW_TIME_RANGE}s.")

    def _findTowFor(self, ts, icao):
        strSql = f"SELECT id FROM logbook_entries " \
                 f"WHERE takeoff_icao = '{icao}' AND aircraft_type IN (2,8) " \
                 f"AND takeoff_ts between ({ts} - {self.TOW_TIME_RANGE}) " \
                 f"AND ({ts} + {self.TOW_TIME_RANGE}) AND tow_id IS NULL " \
                 f"LIMIT 1;"

        with DbSource(dbConnectionInfo).getConnection().cursor() as c:
            c.execute(strSql)
            towId = c.fetchone()

            if towId:
                towId = towId[0]

            return towId

    def gliderTowLookup(self):
        now = int(datetime.now().timestamp())  # [s]
        ts = now - self.TOW_TIME_WINDOW

        strSql = f"SELECT id, address, takeoff_ts, takeoff_icao " \
                 f"FROM logbook_entries " \
                 f"WHERE tow_id IS NULL AND aircraft_type = 1 " \
                 f"AND landing_ts >= {ts};"

        with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
            cur.execute(strSql)

            for row in cur:
                gliderFlightId, address, takeoffTs, takeoffIcao = row

                towFlightId = self._findTowFor(takeoffTs, takeoffIcao)

                if towFlightId:
                    print(f"[INFO] Found tow {towFlightId} for glider {gliderFlightId}")
                    self.queue.put(f"UPDATE logbook_entries set tow_id = {towFlightId} where id = {gliderFlightId};")    # update glider
                    self.queue.put(f"UPDATE logbook_entries set tow_id = {gliderFlightId} where id = {towFlightId};")    # update tow

        if self.queue.qsize() > 0:
            print("[INFO] Num tows discovered: {}".format(int(self.queue.qsize()/2)))    # /2 ~ it's a pair glider-tow plane
            with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
                try:
                    for item in iter(self.queue.get_nowait, None):
                        cur.execute(item)
                except Empty:
                    pass
