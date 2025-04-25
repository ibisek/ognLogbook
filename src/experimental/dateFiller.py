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
from utilsTime import getLocalTzDate

LIMIT = 100


def processLogbookEvents():

    i = 0
    while True:
        with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
            strSql = f'select id, ts, local_date, lat, lon from logbook_events where date is null limit {LIMIT};'

            cur.execute(strSql)
            rows = cur.fetchall()
            if len(rows) == 0:
                break   # uz tu nic neni

            for row in rows:
                eventId, ts, local_date, lat, lon = row

                localDate = getLocalTzDate(utcTs=ts, lat=lat, lon=lon)

                if localDate:
                    updateSql = f"UPDATE logbook_events SET local_date='{localDate}' WHERE id={eventId};"
                    cur.execute(updateSql)

                    if i % 10 == 0:
                        print(f'EVENTS [{i}] updateSql: {updateSql}')

                i += 1


def processLogbookEntries():

    i = 0
    while True:
        with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
            strSql = f'SELECT id, takeoff_ts, takeoff_lat, takeoff_lon, landing_ts, landing_lat, landing_lon, takeoff_date, landing_date from logbook_entries where takeoff_date is null or landing_date is null limit {LIMIT};'

            cur.execute(strSql)
            rows = cur.fetchall()
            if len(rows) == 0:
                break  # uz tu nic neni

            for row in rows:
                entryId, takeoff_ts, takeoff_lat, takeoff_lon, \
                landing_ts, landing_lat, landing_lon, \
                takeoff_date, landing_date = row

                if not takeoff_ts or not landing_ts:
                    continue

                localDateTakeoff = takeoff_date if takeoff_date else getLocalTzDate(utcTs=takeoff_ts, lat=takeoff_lat, lon=takeoff_lon)
                localDateLanding = landing_date if landing_date else getLocalTzDate(utcTs=landing_ts, lat=landing_lat, lon=landing_lon)

                if localDateTakeoff and localDateLanding:
                    updateSql = f"UPDATE logbook_entries SET takeoff_date='{localDateTakeoff}', landing_date='{localDateLanding}' WHERE id={entryId};"
                    cur.execute(updateSql)

                    if i % 10 == 0:
                        print(f'ENTRIES [{i}] updateSql: {updateSql}')

                i += 1


if __name__ == '__main__':

    processLogbookEvents()

    processLogbookEntries()

    print('Hotovo! :)')
