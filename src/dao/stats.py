
from datetime import datetime

from configuration import dbConnectionInfo
from db.DbSource import DbSource
from utilsTime import formatDuration
from utils import getDayTimestamps


def getTotNumFlights():
    num = 0

    try:
        with DbSource(dbConnectionInfo=dbConnectionInfo).getConnection().cursor() as c:
            sql = "SELECT count(address) FROM logbook_entries;"
            res = c.execute(sql)

            if res:
                num = c.fetchone()[0]

    except Exception as ex:
        print('[ERROR] in stats #1:', str(ex))

    return num


def getNumFlightsToday():
    num = 0
    startTs, endTs = getDayTimestamps(datetime.now())

    try:
        with DbSource(dbConnectionInfo=dbConnectionInfo).getConnection().cursor() as c:
            sql = f"SELECT count(address) FROM logbook_entries WHERE takeoff_ts >= {startTs} AND landing_ts <= {endTs};"
            res = c.execute(sql)

            if res:
                num = c.fetchone()[0]

    except Exception as ex:
        print('[ERROR] in stats #2:', str(ex))

    return num


def getLongestFlightToday():
    retVal = (None, None)
    startTs, endTs = getDayTimestamps(datetime.now())

    try:
        with DbSource(dbConnectionInfo=dbConnectionInfo).getConnection().cursor() as c:
            sql = f"SELECT id, flight_time FROM logbook_entries " \
                f"WHERE takeoff_ts >= {startTs} AND landing_ts <= {endTs} " \
                f"ORDER BY flight_time DESC LIMIT 1;"
            res = c.execute(sql)

            if res:
                row = c.fetchone()
                logbookEntryId = row[0]
                seconds = row[1]
                retVal = (logbookEntryId, formatDuration(seconds))

    except Exception as ex:
        print('[ERROR] in stats #3:', str(ex))

    return retVal


def getHighestTrafficToday():
    retVal = None, 0
    startTs, endTs = getDayTimestamps(datetime.now())

    try:
        with DbSource(dbConnectionInfo=dbConnectionInfo).getConnection().cursor() as c:
            sql = f"SELECT location_icao, count(address) AS n FROM logbook_events " \
                f"WHERE ts >= {startTs} AND ts <= {endTs} " \
                f"AND location_icao is not null " \
                f"AND location_icao != 'None' " \
                f"GROUP BY location_icao ORDER BY n DESC LIMIT 1;"
            # .. f"AND location_icao like 'LK%'" \
            res = c.execute(sql)

            if res:
                row = c.fetchone()
                retVal = row[0], row[1]
    except Exception as ex:
        print('[ERROR] in stats #4:', str(ex))

    return retVal

