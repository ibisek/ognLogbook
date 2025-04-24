"""
Doplneni datumovych policek podle timezone v databazi pro zaznamy z minulosti, ktere je jeste nemely vyplnovane.
Jde o nasledujici sloupecky:
    logbook_events.date
    logbook_entries.takeoff_date
    logbook_entries.landing_date

    Za aktualnich (novych) podminek:
    - do logobook_events se to dostane vytvorenim eventu v beaconProcessoru.
    - do logbook_entries to kopiruje DB trigger
"""
from datetime import datetime
import pytz
from tzfpy import get_tz

from configuration import dbConnectionInfo
from db.DbSource import DbSource

LIMIT = 100


def getLocalDate(utcTs: int, lat: float, lon: float) -> str:
    # get landing-local timezone date:
    tzStr = get_tz(lon, lat)  # !! order LON , LAT !!
    tzInfo = pytz.timezone(tzStr)
    dtLocal = datetime.fromtimestamp(utcTs, tz=tzInfo)
    dateLocal = dtLocal.strftime('%Y-%m-%d')

    return dateLocal


def processLogbookEvents():

    i = 0
    while True:
        with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
            strSql = f'select id, ts, date, lat, lon from logbook_events where date is null limit {LIMIT};'

            cur.execute(strSql)
            rows = cur.fetchall()
            if len(rows) == 0:
                break   # uz tu nic neni

            for row in rows:
                eventId, ts, date, lat, lon = row

                dateLocal = getLocalDate(ts, lat, lon)

                updateSql = f"UPDATE logbook_events SET date='{dateLocal}' WHERE id={eventId};"
                cur.execute(updateSql)

                if i % 10 == 0:
                    print(f'EVENTS [{i}] updateSql: {updateSql}')

                i += 1


def processLogbookEntries():

    i = 0
    while True:
        with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
            strSql = f'SELECT id, takeoff_ts, takeoff_lat, takeoff_lon, landing_ts, landing_lat, landing_lon from logbook_entries where takeoff_date is null or landing_date is null limit {LIMIT};'

            cur.execute(strSql)
            rows = cur.fetchall()
            if len(rows) == 0:
                break  # uz tu nic neni

            for row in rows:
                entryId, takeoff_ts, takeoff_lat, takeoff_lon, landing_ts, landing_lat, landing_lon = row

                if not takeoff_ts or not landing_ts:
                    continue

                dateLocalTakeoff = getLocalDate(takeoff_ts, takeoff_lat, takeoff_lon)
                dateLocalLanding = getLocalDate(landing_ts, landing_lat, landing_lon)

                updateSql = f"UPDATE logbook_entries SET takeoff_date='{dateLocalTakeoff}', landing_date='{dateLocalLanding}' WHERE id={entryId};"
                cur.execute(updateSql)

                if i % 10 == 0:
                    print(f'ENTRIES [{i}] updateSql: {updateSql}')

                i += 1


if __name__ == '__main__':

    processLogbookEvents()

    processLogbookEntries()

    print('Hotovo! :)')
