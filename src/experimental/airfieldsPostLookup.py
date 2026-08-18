"""
A tool to replenish missing ICAO records in the logbook_entries table.
Can be used after airfields.json got extended by new locations.
"""

import logging
import os

from datetime import datetime, timezone, timedelta
from time import sleep

from airfieldManager import AirfieldManager
from configuration import dbConnectionInfo
from db.DbSource import DbSource
from db.DbThread import DbThread


def _waitUntilCpuLoadLow():
    # load1, load5, load15 = os.getloadavg()
    while normalizedLoad := os.getloadavg()[1] / (os.cpu_count() or 1) > 1:
        logging.info('Waiting for lower CPU load')
        sleep(60)


def _getTsLimit():
    now = datetime.now(tz=timezone.utc) - timedelta(days=60)
    return int(now.timestamp())


def _processLogbookEvents():
    _waitUntilCpuLoadLow()

    strSql = f'SELECT id, location_icao, lat, lon FROM logbook_events WHERE location_icao IS null AND ts >= {_getTsLimit()};'

    cur = dbs.getConnection().cursor()
    cur.execute(strSql)

    numUpdatedRecords = 0

    for row in cur:
        (id, icao, lat, lon) = row

        if not icao and lat and lon:
            icao, distKm = afm.getNearest2(lat, lon, calcDistance=True)
            if icao and distKm < AirfieldManager.MIN_DIST_FROM_AIRFIELD:
                print('locationIcao:', icao)
                strSql = f"UPDATE logbook_events set location_icao = '{icao}' where id = {id}"
                dbt.addStatement(strSql)
                numUpdatedRecords += 1

        _waitUntilCpuLoadLow()

    print('LE numUpdatedRecords:', numUpdatedRecords)

    return numUpdatedRecords


def _processLogbookEntries():
    _waitUntilCpuLoadLow()

    strSql = f"SELECT id, takeoff_icao, takeoff_lat, takeoff_lon, landing_icao, landing_lat, landing_lon FROM logbook_entries " \
             f"WHERE takeoff_icao IS null OR landing_icao IS null AND takeoff_ts >= {_getTsLimit()};"
    cur = dbs.getConnection().cursor()
    cur.execute(strSql)

    numUpdatedRecords = 0

    for row in cur:
        (id, takeoffIcao, takeoffLat, takeoffLon, landingIcao, landingLat, landingLon) = row

        if not takeoffIcao and takeoffLat and takeoffLon:
            takeoffIcao, distKm = afm.getNearest2(takeoffLat, takeoffLon, calcDistance=True)
            if takeoffIcao and distKm < AirfieldManager.MIN_DIST_FROM_AIRFIELD:
                print('takeoffIcao:', takeoffIcao)
                strSql = f"UPDATE logbook_entries set takeoff_icao = '{takeoffIcao}' where id = {id}"
                dbt.addStatement(strSql)
                numUpdatedRecords += 1

        if not landingIcao and landingLat and landingLon:
            landingIcao, distKm = afm.getNearest2(landingLat, landingLon, calcDistance=True)
            if landingIcao and distKm < AirfieldManager.MIN_DIST_FROM_AIRFIELD:
                print('landingIcao:', landingIcao)
                strSql = f"UPDATE logbook_entries set landing_icao = '{landingIcao}' where id = {id}"
                dbt.addStatement(strSql)
                numUpdatedRecords += 1

        _waitUntilCpuLoadLow()

    print('numUpdatedRecords:', numUpdatedRecords)

    return numUpdatedRecords


if __name__ == '__main__':

    afm = AirfieldManager()

    dbt = DbThread(dbConnectionInfo=dbConnectionInfo)
    dbt.start()

    dbs = DbSource(dbConnectionInfo=dbConnectionInfo)

    _processLogbookEvents()     # take-offs and landings
    _processLogbookEntries()   # flights

    while not dbt.toDoStatements.empty():
        print('len DB toDoStatements:', dbt.toDoStatements.qsize())
        sleep(1)
    dbt.stop()

    print('KOHEU.')
