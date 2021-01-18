"""
A tool to replenish missing ICAO records in the logbook_entries table.
Can be used after airfields.json got extended by new locations.
"""

from time import sleep

from airfieldManager import AirfieldManager
from configuration import dbConnectionInfo
from db.DbSource import DbSource
from db.DbThread import DbThread


def _processLogbookEvents():
    strSql = 'SELECT id, location_icao, lat, lon FROM logbook_events WHERE location_icao IS null;'

    cur = dbs.getConnection().cursor()
    cur.execute(strSql)

    numUpdatedRecords = 0

    for row in cur:
        (id, icao, lat, lon) = row

        if not icao and lat and lon:
            icao = afm.getNearest(lat, lon)
            if icao:
                print('locationIcao:', icao)
                strSql = f"UPDATE logbook_events set location_icao = '{icao}' where id = {id}"
                dbt.addStatement(strSql)
                numUpdatedRecords += 1

    print('LE numUpdatedRecords:', numUpdatedRecords)


def _processLogbookEntries():
    strSql = 'SELECT id, takeoff_icao, takeoff_lat, takeoff_lon, landing_icao, landing_lat, landing_lon FROM logbook_entries ' \
             'WHERE takeoff_icao IS null OR landing_icao IS null;'
    cur = dbs.getConnection().cursor()
    cur.execute(strSql)

    numUpdatedRecords = 0

    for row in cur:
        (id, takeoffIcao, takeoffLat, takeoffLon, landingIcao, landingLat, landingLon) = row

        if not takeoffIcao and takeoffLat and takeoffLon:
            takeoffIcao = afm.getNearest(takeoffLat, takeoffLon)
            if takeoffIcao:
                print('takeoffIcao:', takeoffIcao)
                strSql = f"UPDATE logbook_entries set takeoff_icao = '{takeoffIcao}' where id = {id}"
                dbt.addStatement(strSql)
                numUpdatedRecords += 1

        if not landingIcao and landingLat and landingLon:
            landingIcao = afm.getNearest(landingLat, landingLon)
            if landingIcao:
                print('landingIcao:', landingIcao)
                strSql = f"UPDATE logbook_entries set landing_icao = '{landingIcao}' where id = {id}"
                dbt.addStatement(strSql)
                numUpdatedRecords += 1

    print('numUpdatedRecords:', numUpdatedRecords)


if __name__ == '__main__':

    afm = AirfieldManager()

    dbt = DbThread(dbConnectionInfo=dbConnectionInfo)
    dbt.start()

    dbs = DbSource(dbConnectionInfo=dbConnectionInfo)

    _processLogbookEntries()    # take-offs and landings
    _processLogbookEvents()     # flights

    while len(dbt.toDoStatements) > 0:
        print('len DB toDoStatements:', len(dbt.toDoStatements))
        sleep(1)
    dbt.stop()

    print('KOHEU.')
