
from configuration import dbConnectionInfo
from db.DbSource import DbSource
from utils import formatDuration, getDayTimestamps


def getTotNumFlights():
    num = None

    try:
        with DbSource(dbConnectionInfo=dbConnectionInfo).getConnection() as c:
            sql = "SELECT count(address) FROM logbook_entries;"
            res = c.execute(sql)

            if res:
                num = c.fetchone()[0]

    except Exception as ex:
        print('[ERROR] in stats #1:', str(ex))

    return num


def getNumFlightsToday():
    num = None
    startTs, endTs = getDayTimestamps()

    try:
        with DbSource(dbConnectionInfo=dbConnectionInfo).getConnection() as c:
            sql = f"SELECT count(address) FROM logbook_entries WHERE takeoff_ts >= {startTs} AND landing_ts <= {endTs};"
            res = c.execute(sql)

            if res:
                num = c.fetchone()[0]

    except Exception as ex:
        print('[ERROR] in stats #2:', str(ex))

    return num


def getLongestFlightTimeToday():
    retVal = None
    startTs, endTs = getDayTimestamps()

    try:
        with DbSource(dbConnectionInfo=dbConnectionInfo).getConnection() as c:
            sql = f"SELECT flight_time FROM logbook_entries " \
                f"WHERE takeoff_ts >= {startTs} AND landing_ts <= {endTs} " \
                f"ORDER BY flight_time DESC LIMIT 1;"
            res = c.execute(sql)

            if res:
                seconds = c.fetchone()[0]
                retVal = formatDuration(seconds)

    except Exception as ex:
        print('[ERROR] in stats #3:', str(ex))

    return retVal


def getHighestTrafficToday():
    retVal = None, 0
    startTs, endTs = getDayTimestamps()

    try:
        with DbSource(dbConnectionInfo=dbConnectionInfo).getConnection() as c:
            sql = f"SELECT location_icao, count(address) AS n FROM logbook_events " \
                f"WHERE ts >= {startTs} AND ts <= {endTs} " \
                f"GROUP BY location_icao ORDER BY n DESC LIMIT 1;"
            # .. f"AND location_icao like 'LK%'" \
            res = c.execute(sql)

            if res:
                row = c.fetchone()
                retVal = row[0], row[1]
    except Exception as ex:
        print('[ERROR] in stats #4:', str(ex))

    return retVal

