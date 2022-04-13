from datetime import datetime

from configuration import dbConnectionInfo
from db.DbSource import DbSource
from dataStructures import LogbookItem
from utils import getDayTimestamps


def _prepareCondition(address=None, icaoCode=None, registration=None):
    c1 = c2 = ''
    if icaoCode:
        c1 = f" AND l.location_icao = '{icaoCode}'"
    if registration:
        c2 = f" AND d.aircraft_registration = '{registration}'"
    cond = c1 + c2

    return cond


def listDepartures(address=None, icaoCode=None, registration=None, forDay=None, limit=None, icaoFilter: list = [],
                   sortTsDesc=False):
    cond = _prepareCondition(address=address, icaoCode=icaoCode, registration=registration)

    condTs = ''
    condLimit = ''
    startTs, endTs = getDayTimestamps(forDay)
    if startTs and endTs:
        condTs = f" AND l.ts >= {startTs} AND l.ts <= {endTs}"

    if limit:
        condLimit = f" limit {limit}"

    condIcao = ''
    if len(icaoFilter) > 0:
        c = ""
        for i, prefix in enumerate(icaoFilter):
            c += f"l.location_icao LIKE '{prefix}%'"
            if i < (len(icaoFilter) - 1):
                c += ' OR '
        condIcao += f" AND ({c})"

    sortTs = 'DESC' if sortTsDesc else 'ASC'

    records = list()

    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:

        # (d.tracked != false OR d.tracked IS NULL) AND (d.identified != false OR d.identified IS NULL)
        strSql = f"""SELECT l.ts, l.address, l.address_type, l.aircraft_type, l.lat, l.lon, l.location_icao, 
                    d.device_type,	d.aircraft_type, d.aircraft_registration, d.aircraft_cn 
                    FROM logbook_events AS l 
                    LEFT JOIN ddb AS d ON l.address = d.device_id 
                    WHERE l.event = 'T' AND 1 {cond} {condTs} {condIcao}
                    AND not (l.location_icao is null AND d.aircraft_registration is null)
                    ORDER by ts {sortTs} {condLimit};"""

        cur.execute(strSql)

        rows = cur.fetchall()
        for row in rows:
            (ts, address, addrType, aircraftTypeCode, lat, lon, locationIcao, devType, aircraftType, registration,
             cn) = row

            item = LogbookItem(id=None,
                               address=address,
                               takeoff_ts=ts,
                               takeoff_lat=float(lat),
                               takeoff_lon=float(lon),
                               takeoff_icao=locationIcao,
                               landing_ts=0,
                               landing_lat=0,
                               landing_lon=0,
                               landing_icao=None,
                               flight_time=0,
                               registration=registration,
                               cn=cn,
                               aircraft_type=aircraftType)

            records.append(item)

    return records


def listArrivals(address=None, icaoCode=None, registration=None, forDay=None, limit=None, icaoFilter: list = [],
                 sortTsDesc=False):
    cond = _prepareCondition(address=address, icaoCode=icaoCode, registration=registration)

    condTs = ''
    condLimit = ''
    startTs, endTs = getDayTimestamps(forDay)
    if startTs and endTs:
        condTs = f" AND l.ts >= {startTs} AND l.ts <= {endTs}"

    if limit:
        condLimit = f" limit {limit}"

    condIcao = ''
    if len(icaoFilter) > 0:
        c = ""
        for i, prefix in enumerate(icaoFilter):
            c += f"l.location_icao LIKE '{prefix}%'"
            if i < (len(icaoFilter) - 1):
                c += ' OR '
        condIcao += f" AND ({c})"

    sortTs = 'DESC' if sortTsDesc else 'ASC'

    records = list()

    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:

        # (d.tracked != false OR d.tracked IS NULL) AND (d.identified != false OR d.identified IS NULL)
        strSql = f"""SELECT l.ts, l.address, l.address_type, l.aircraft_type, l.lat, l.lon, l.location_icao, l.flight_time,
                    d.device_type,	d.aircraft_type, d.aircraft_registration, d.aircraft_cn 
                    FROM logbook_events AS l 
                    LEFT JOIN ddb AS d ON l.address = d.device_id 
                    WHERE l.event = 'L' AND 1 {cond} {condTs} {condIcao}
                    AND not (l.location_icao is null AND d.aircraft_registration is null)
                    ORDER by ts {sortTs} {condLimit};"""

        cur.execute(strSql)

        rows = cur.fetchall()
        for row in rows:
            (ts, address, addrType, aircraftTypeCode, lat, lon, locationIcao, flightTime, devType, aircraftType,
             registration, cn) = row

            item = LogbookItem(id=None,
                               address=address,
                               takeoff_ts=0,
                               takeoff_lat=0,
                               takeoff_lon=0,
                               takeoff_icao=None,
                               landing_ts=ts,
                               landing_lat=float(lat),
                               landing_lon=float(lon),
                               landing_icao=locationIcao,
                               flight_time=flightTime,
                               device_type=devType,
                               registration=registration,
                               cn=cn,
                               aircraft_type=aircraftType)

            records.append(item)

    return records


def listFlights(address=None, icaoCode=None, registration=None, forDay=None, limit=None, icaoFilter: list = [],
                sortTsDesc=False, orderByCol='takeoff_ts'):
    c1 = c2 = ''
    if icaoCode:
        c1 = f" AND (l.takeoff_icao = '{icaoCode}' OR l.landing_icao = '{icaoCode}')"
    if registration:
        c2 = f" AND d.aircraft_registration = '{registration}'"
    cond = c1 + c2

    condTs = ''
    condLimit = ''
    startTs, endTs = getDayTimestamps(forDay)
    if startTs and endTs:
        condTs = f" AND l.takeoff_ts >= {startTs} AND l.landing_ts <= {endTs}"

    if limit:
        condLimit = f" limit {limit}"

    condIcao = ''
    if len(icaoFilter) > 0:
        c = ""
        for i, prefix in enumerate(icaoFilter):
            c += f"l.takeoff_icao LIKE '{prefix}%' OR l.landing_icao like '{prefix}%'"
            if i < (len(icaoFilter) - 1):
                c += ' OR '

        condIcao += f" AND ({c})"

    sortTs = 'DESC' if sortTsDesc else 'ASC'

    records = list()

    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:

        # (d.tracked != false OR d.tracked IS NULL) AND (d.identified != false OR d.identified IS NULL)
        strSql = f"""SELECT l.id, l.address, l.takeoff_ts, l.takeoff_lat, l.takeoff_lon, l.takeoff_icao, 
                    l.landing_ts, l.landing_lat, l.landing_lon, l.landing_icao, l.flight_time, l.flown_distance, l.tow_id,
                    d.device_type, d.aircraft_type, d.aircraft_registration, d.aircraft_cn
                    FROM logbook_entries as l 
                    LEFT JOIN ddb AS d ON l.address = d.device_id
                    WHERE l.hidden is false {cond} {condTs} {condIcao} 
                    AND not (l.takeoff_icao is null AND l.landing_icao is null AND d.aircraft_registration is null)
                    ORDER by {orderByCol} {sortTs} {condLimit};"""

        cur.execute(strSql)

        rows = cur.fetchall()
        for row in rows:
            (id, address, ts1, lat1, lon1, locationIcao1, ts2, lat2, lon2, locationIcao2, flightTime, flownDistance,
             towId, devType, aircraftType, registration, cn) = row

            item = LogbookItem(id=id,
                               address=address,
                               takeoff_ts=ts1 if ts1 else None,
                               takeoff_lat=float(lat1) if lat1 else None,
                               takeoff_lon=float(lon1) if lon1 else None,
                               takeoff_icao=locationIcao1 if locationIcao1 else None,
                               landing_ts=ts2,
                               landing_lat=float(lat2),
                               landing_lon=float(lon2),
                               landing_icao=locationIcao2,
                               flight_time=flightTime,
                               flown_distance=flownDistance,
                               device_type=devType,
                               registration=registration,
                               cn=cn,
                               aircraft_type=aircraftType,
                               tow_id=towId)

            records.append(item)

    return records


def getFlight(flightId) -> LogbookItem:
    """
    Used by map view.
    :param flightId:
    :return: basic information about specified flight
    """
    strSql = f"SELECT le.address, le.address_type, le.takeoff_ts, le.landing_ts, le.takeoff_icao, le.landing_icao, " \
             f"le.flight_time, le.flown_distance, d.aircraft_type, d.aircraft_registration, d.aircraft_cn " \
             "FROM logbook_entries AS le " \
             "LEFT JOIN ddb as d ON le.address = d.device_id " \
             f"WHERE le.id={flightId}"
    with DbSource(dbConnectionInfo).getConnection().cursor() as c:
        c.execute(strSql)
        row = c.fetchone()
        if row:
            address, address_type, takeoff_ts, landing_ts, takeoff_icao, landing_icao, flight_time, flown_distance, aircraft_type, registration, cn = row
            return LogbookItem(id=flightId, address=address, address_type=address_type,
                               takeoff_ts=takeoff_ts, landing_ts=landing_ts,
                               takeoff_icao=takeoff_icao, landing_icao=landing_icao,
                               flight_time=flight_time, flown_distance=flown_distance,
                               aircraft_type=aircraft_type, registration=registration, cn=cn)

    return None


def getSums(registration, forDay=None, limit=None):
    cond = f" AND d.aircraft_registration='{registration}'"

    condTs = ''
    startTs, endTs = getDayTimestamps(forDay)
    if startTs and endTs:
        condTs = f" AND l.takeoff_ts >= {startTs} AND l.landing_ts <= {endTs}"

    numFlights = 0
    totalFlightTime = 0

    with DbSource(dbConnectionInfo).getConnection().cursor() as c:

        strSql = f"""SELECT COUNT(l.address) AS num, SUM(l.flight_time) AS time
                        FROM logbook_entries as l 
                        LEFT JOIN ddb AS d ON l.address = d.device_id
                        WHERE hidden is false AND tracked = true AND identified = true {cond} {condTs}
                        ORDER by landing_ts desc;"""

        c.execute(strSql)

        row = c.fetchall()

        if row:
            numFlights = row[0][0]
            totalFlightTime = row[0][1]  # [s]

    return numFlights, totalFlightTime


def findMostRecentTakeoff(address: str, addressType: int) -> LogbookItem:
    strSql = f"SELECT id, ts, address, address_type, aircraft_type, event, lat, lon, location_icao " \
             f"FROM logbook_events " \
             f"WHERE address = '{address}' AND address_type={addressType} AND event='T' " \
             f"ORDER by ts DESC LIMIT 1;"

    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
        cur.execute(strSql)
        row = cur.fetchone()
        if row:
            id, ts, address, addressType, aircraftType, event, lat, lon, location = row

            item = LogbookItem(id=id,
                               address=address,
                               address_type=addressType,
                               aircraft_type=aircraftType,
                               takeoff_ts=ts,
                               takeoff_lat=lat,
                               takeoff_lon=lon,
                               takeoff_icao=location)

            return item

    return None


def getNumStatsPerDay(forDay: datetime = None):
    """
    @return numFlights, totalFlightTime [s]
    """
    startTs, endTs = getDayTimestamps(forDay)
    if not startTs or not endTs:
        return None, None

    numFlights = 0
    totalFlightTime = 0

    with DbSource(dbConnectionInfo).getConnection().cursor() as c:
        strSql = f"""SELECT count(id), sum(flight_time) FROM logbook_entries 
            WHERE takeoff_ts >= {startTs} AND landing_ts <= {endTs};"""

        c.execute(strSql)
        row = c.fetchall()
        if row:
            numFlights = float(row[0][0])
            totalFlightTime = float(row[0][1])  # [s]

    return numFlights, totalFlightTime
