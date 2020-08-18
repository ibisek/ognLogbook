"""
A tool to replenish missing ICAO records in the logbook_entries table.
Can be used after airfields.json got extended by new locations.
"""

from time import sleep

from airfieldManager import AirfieldManager
from configuration import dbConnectionInfo
from db.DbSource import DbSource
from db.DbThread import DbThread

if __name__ == '__main__':

    afm = AirfieldManager()

    dbt = DbThread(dbConnectionInfo=dbConnectionInfo)
    dbt.start()

    dbs = DbSource(dbConnectionInfo=dbConnectionInfo)

    strSql = 'select id, takeoff_icao, takeoff_lat, takeoff_lon, landing_icao, landing_lat, landing_lon from logbook_entries where takeoff_icao is null or landing_icao is null;'
    cur = dbs.getConnection().cursor()
    cur.execute(strSql)

    numUpdatedRecords = 0

    for row in cur.fetchall():
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

    print('numUpdatedRecords:', 0)

    while len(dbt.toDoStatements) > 0:
        print('len DB toDoStatements:', len(dbt.toDoStatements))
        sleep(1)
    dbt.stop()

    print('KOHEU.')
