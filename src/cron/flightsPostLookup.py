
"""
Tool to find flights that were not closed/created.
For an airplane there exists takeoff event but no landing and thus also no flight.

It works in the following steps:
#1 find a takeoff without appropriate landing,
#2 check in redis the airplane is not airborne (i.e. its state is landed or no status record in redis,
#3 from influx load appropriate flight data,
#4 find the landing or use last fix when there was no OGN coverage,
#5 create a LANDING event in tne logbook_events table.
"""

from datetime import datetime, timezone, timedelta
from redis import StrictRedis
from typing import List

from airfieldManager import AirfieldManager
from configuration import dbConnectionInfo, redisConfig, INFLUX_DB_NAME, INFLUX_DB_HOST, ADDRESS_TYPE_PREFIX_LETTER
from dataStructures import LogbookEvent, Status
from db.DbSource import DbSource
from db.InfluxDbThread import InfluxDbThread


class FlightsPostLookup:
    RUN_INTERVAL = 12 * 3600   # [s]

    def __init__(self):
        self.redis = StrictRedis(**redisConfig)
        self.influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST, startThread=False)
        self.afm = AirfieldManager()

        self.running = False

    def __del__(self):
        if self.influxDb:
            self.influxDb.client.close()

    def _findTakeoffsWithoutLanding(self, date: datetime) -> List[LogbookEvent]:
        dateFormatted = date.strftime('%Y-%m-%d')

        q = f"""SELECT ts, address, address_type, aircraft_type FROM logbook_events as e
        WHERE 
            e.event = 'T'
            AND local_date='{dateFormatted}' 
            AND NOT EXISTS (
                SELECT 1  FROM logbook_events ee WHERE 
                    ee.address_type = e.address_type
                    AND ee.address = e.address
                  AND ee.event = 'L' 
                  AND ee.ts > e.ts
            )
        ORDER BY e.ts;
        """

        events = []

        connection = DbSource(dbConnectionInfo).getConnection()
        cur = connection.cursor()
        cur.execute(q)
        while row := cur.fetchone():
            ts, addr, addrType, aircraftType = row

            event = LogbookEvent()
            event.type = 'T'
            event.ts = ts
            event.localDate = dateFormatted
            event.address = addr
            event.addressType = addrType
            event.aircraftType = aircraftType

            events.append(event)

        return events

    def _omitAirborneCrafts(self, takeOffEvents: List[LogbookEvent]) -> List[LogbookEvent]:
        takeOffsWithoutLandings: List[LogbookEvent] = []

        for e in takeOffEvents:
            # check status in redis:
            statusKey = f"{e.addressType}{e.address}-status"
            res = self.redis.get(statusKey)
            if not res:
                takeOffsWithoutLandings.append(e)
            else:
                s = Status.parse(res.decode('utf-8'))
                if not s.airborne():
                    takeOffsWithoutLandings.append(e)

        return takeOffsWithoutLandings

    def _findLandingEvent(self, takeOffsWithoutLandings: List[LogbookEvent]):
        landingEvents = []

        for e in takeOffsWithoutLandings:
            addressTypeStr = ADDRESS_TYPE_PREFIX_LETTER.get(e.addressType, None)
            windowStartTs = e.ts + 60       # [s]    one minute after take-off
            windowEndTs = e.ts + 12 * 3600  # [s] at most 12h after take-off

            q = f"SELECT * FROM pos WHERE addr='{addressTypeStr}{e.address}' AND time >= {windowStartTs}000000000 and time <= {windowEndTs}000000000"

            rs = self.influxDb.query(q)

            if rs:
                rows = [row for row in rs.get_points()]

                landingOrLostIndex = -1
                for i, row in enumerate(rows):
                    groundSpeed = row['gs']
                    agl = row.get('agl', 111e+111)
                    if groundSpeed <= 80 or agl < 300:  # getGroundSpeedThreshold(logbookItem.aircraft_type, forEvent='T'):
                        landingOrLostIndex = i

                finalFixRow = rows[landingOrLostIndex]

                landingTs = int(datetime.strptime(finalFixRow['time'], '%Y-%m-%dT%H:%M:%S%z').timestamp())  # UTC
                flightTime = landingTs - e.ts

                e.type = 'L'
                e.flightTime = flightTime
                e.ts = landingTs
                e.lat = float(finalFixRow.get('lat', -1))
                e.lon = float(finalFixRow.get('lon', -1))
                e.icaoLocation = self.afm.getNearest(e.lat, e.lon)

                landingEvents.append(e)

        return landingEvents

    def _createLandingEvents(self, landingEvents: List[LogbookEvent]):
        for e in landingEvents:
            strSql = f"INSERT INTO logbook_events " \
                     f"(ts, local_date, address, address_type, aircraft_type, event, lat, lon, location_icao, flight_time) " \
                     f"VALUES " \
                     f"({e.ts}, '{e.localDate}', '{e.address}', '{e.addressType}', '{e.aircraftType}', " \
                     f"'{e.type}', {e.lat:.5f}, {e.lon:.5f}, '{e.icaoLocation}', {e.flightTime});"

            connection = DbSource(dbConnectionInfo).getConnection()
            cur = connection.cursor()
            cur.execute(strSql)

            formattedDt = datetime.fromtimestamp(e.ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
            loc = e.icaoLocation if e.icaoLocation else f"[{e.lat:.4f}; {e.lon:.4f}]"
            print(f"[INFO] Created landing event for '{ADDRESS_TYPE_PREFIX_LETTER.get(e.addressType, '?')} {e.address}' on {formattedDt} near {loc}.")

    def doWork(self):
        """
        To be executed by logbook's CRON loop.
        """
        if self.running:
            return

        date = datetime.now(timezone.utc) - timedelta(1)

        try:
            self.running = True
            takeOffEvents = self._findTakeoffsWithoutLanding(date=date)
            takeOffsWithoutLandings = fpl._omitAirborneCrafts(takeOffEvents=takeOffEvents)
            landingEvents = fpl._findLandingEvent(takeOffsWithoutLandings=takeOffsWithoutLandings)
            fpl._createLandingEvents(landingEvents=landingEvents)
        finally:
            self.running = False


if __name__ == '__main__':
    fpl = FlightsPostLookup()
    fpl.doWork()

    print('Done.')
