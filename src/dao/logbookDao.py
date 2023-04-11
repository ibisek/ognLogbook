from datetime import datetime
import pytz

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
                   sortTsDesc=False, display_tz=pytz.utc):
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
        strSql = f"""SELECT l.id, l.ts, l.address, l.address_type, l.aircraft_type, l.lat, l.lon, l.location_icao, l.in_ps,
                    d.device_type,	d.aircraft_type, d.aircraft_registration, d.aircraft_cn 
                    FROM logbook_events AS l 
                    LEFT JOIN ddb AS d ON l.address = d.device_id 
                    WHERE l.event = 'T' AND 1 {cond} {condTs} {condIcao}
                    AND not (l.location_icao is null AND d.aircraft_registration is null)
                    ORDER by ts {sortTs} {condLimit};"""

        cur.execute(strSql)

        rows = cur.fetchall()
        for row in rows:
            (eventId, ts, address, addrType, aircraftTypeCode, lat, lon, locationIcao, in_ps, devType, aircraftType, registration, cn) = row

            item = LogbookItem(id=eventId,
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
                               in_ps=in_ps,
                               registration=registration,
                               cn=cn,
                               aircraft_type=aircraftType,
                               display_tz=display_tz)

            records.append(item)

    return records


def listArrivals(address=None, icaoCode=None, registration=None, forDay=None, limit=None, icaoFilter: list = [],
                 sortTsDesc=False, display_tz=pytz.utc):
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
                    l.flight_time, l.in_ps,
                    d.device_type,	d.aircraft_type, d.aircraft_registration, d.aircraft_cn 
                    FROM logbook_events AS l 
                    LEFT JOIN ddb AS d ON l.address = d.device_id 
                    WHERE l.event = 'L' AND 1 {cond} {condTs} {condIcao}
                    AND not (l.location_icao is null AND d.aircraft_registration is null)
                    ORDER by ts {sortTs} {condLimit};"""

        cur.execute(strSql)

        rows = cur.fetchall()
        for row in rows:
            (ts, address, addrType, aircraftTypeCode, lat, lon, locationIcao, flightTime, in_ps, devType, aircraftType,
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
                               in_ps=in_ps,
                               flight_time=flightTime,
                               device_type=devType,
                               registration=registration,
                               cn=cn,
                               aircraft_type=aircraftType,
                               display_tz=display_tz)

            records.append(item)

    return records


def listFlights(address=None, icaoCode=None, registration=None, forDay=None, limit=None, icaoFilter: list = [],
                sortTsDesc=False, orderByCol='takeoff_ts', display_tz=pytz.utc):
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
                    l.landing_ts, l.landing_lat, l.landing_lon, l.landing_icao, l.flight_time, l.flown_distance, l.tow_id, l.in_ps,
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
             towId, in_ps, devType, aircraftType, registration, cn) = row

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
                               in_ps=in_ps,
                               device_type=devType,
                               registration=registration,
                               cn=cn,
                               aircraft_type=aircraftType,
                               tow_id=towId,
                               display_tz=display_tz)

            records.append(item)

    return records


def getFlight(flightId, display_tz=pytz.utc) -> LogbookItem:
    """
    Used by map view.
    :param flightId:
    :param display_tz:
    :return: basic information about specified flight
    """
    strSql = f"SELECT le.address, le.address_type, le.takeoff_ts, le.landing_ts, le.takeoff_icao, le.landing_icao, " \
             f"le.flight_time, le.flown_distance, le.in_ps, d.aircraft_type, d.aircraft_registration, d.aircraft_cn " \
             "FROM logbook_entries AS le " \
             "LEFT JOIN ddb as d ON le.address = d.device_id " \
             f"WHERE le.id={flightId}"
    with DbSource(dbConnectionInfo).getConnection().cursor() as c:
        c.execute(strSql)
        row = c.fetchone()
        if row:
            address, address_type, takeoff_ts, landing_ts, takeoff_icao, landing_icao, flight_time, flown_distance, in_ps, aircraft_type, registration, cn = row
            return LogbookItem(id=flightId, address=address, address_type=address_type,
                               takeoff_ts=takeoff_ts, landing_ts=landing_ts,
                               takeoff_icao=takeoff_icao, landing_icao=landing_icao,
                               flight_time=flight_time, flown_distance=flown_distance, in_ps=in_ps,
                               aircraft_type=aircraft_type, registration=registration, cn=cn,
                               display_tz=display_tz)

    return None


def getFlightIdForTakeoffId(takeoffId) -> LogbookItem:
    """
    Used when looking up a complete flight for specified takeoffId
    :param takeoffId:
    """
    strSql = f"SELECT ent.id FROM logbook_entries AS ent, logbook_events AS ev " \
             f"WHERE ent.address = ev.address AND ent.takeoff_ts = ev.ts " \
             f"AND ev.id={takeoffId};"

    with DbSource(dbConnectionInfo).getConnection().cursor() as c:
        c.execute(strSql)
        row = c.fetchone()
        if row:
            return row[0]   # flightId

    return None


def getFlightInfoForTakeoff(takeoffId, display_tz:pytz.utc) -> LogbookItem:
    """
    :param takeoffId: ID of a take-off event
    :param display_tz:
    :return a not-completely-populated LogbookItem for requested takeoffId (event ID for take-off)
    """
    strSql = f"SELECT e.ts, e.address, e.address_type, e.in_ps, d.aircraft_type, d.aircraft_registration, d.aircraft_cn " \
             f"FROM logbook_events AS e " \
             f"LEFT JOIN ddb AS d ON e.address = d.device_id " \
             f"WHERE e.event='T' AND e.id={takeoffId};"

    with DbSource(dbConnectionInfo).getConnection().cursor() as c:
        c.execute(strSql)
        row = c.fetchone()
        if row:
            takeoff_ts, address, address_type, in_ps, aircraft_type, registration, cn = row

            return LogbookItem(id=takeoffId,
                               address=address, address_type=address_type,
                               takeoff_ts=takeoff_ts, in_ps=in_ps,
                               aircraft_type=aircraft_type, registration=registration, cn=cn,
                               display_tz=display_tz)

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


def findMostRecentTakeoff(address: str, addressType: str, display_tz: pytz.utc) -> LogbookItem:
    strSql = f"SELECT id, ts, address, address_type, aircraft_type, event, lat, lon, location_icao " \
             f"FROM logbook_events " \
             f"WHERE address = '{address}' AND address_type='{addressType}' AND event='T' " \
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
                               takeoff_icao=location,
                               display_tz=display_tz)

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
