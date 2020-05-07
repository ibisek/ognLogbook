"""
Downloads current database from
    https://ddb.glidernet.org/download/
and updates records in the local DB.
"""

import csv
import sys
import requests

from configuration import dbConnectionInfo
from db.DbSource import DbSource

DDB_URL = 'https://ddb.glidernet.org/download/'


def _dropAllDdbRecords():
    with DbSource(dbConnectionInfo).getConnection() as cur:
        cur.execute("DELETE FROM ddb;")


if __name__ == '__main__':

    resp = requests.get(DDB_URL)

    if resp.status_code != 200:
        print(f"[WARN] Download of the datafile failed with code {resp.status_code}")
        sys.exit(1)

    lines = resp.text.split('\n')

    if len(lines) < 10000:
        sys.exit(1)

    _dropAllDdbRecords();
    keys = lines[0].strip().replace('#', '').split(',')

    for i in range(1, len(lines)):
        items = lines[i].strip().replace('\'', '').split(',')
        print(f"[INFO] items: {items}")

        if len(items) != len(keys):
            continue

        deviceType = items[keys.index('DEVICE_TYPE')]   # F/O/I
        deviceId = items[keys.index('DEVICE_ID')]       # xxyyzz
        aircraftType = items[keys.index('AIRCRAFT_MODEL')]  # string (32)
        registration = items[keys.index('REGISTRATION')]    # string (10)
        cn = items[keys.index('CN')]                        # string (3)
        tracked = True if items[keys.index('TRACKED')] == 'Y' else False
        identified = True if items[keys.index('IDENTIFIED')] == 'Y' else False

        strSql = f"INSERT INTO ddb " \
                 f"(device_type, device_id, aircraft_type, aircraft_registration, aircraft_cn, tracked, identified)" \
                 f"VALUES " \
                 f"(%(device_type)s, %(device_id)s, %(aircraft_type)s, %(aircraft_registration)s, %(aircraft_cn)s, %(tracked)s, %(identified)s);"

        data = dict()
        data['device_type'] = deviceType
        data['device_id'] = deviceId
        data['aircraft_type'] = aircraftType
        data['aircraft_registration'] = registration
        data['aircraft_cn'] = cn
        data['tracked'] = tracked
        data['identified'] = identified

        with DbSource(dbConnectionInfo).getConnection() as cur:
            cur.execute(strSql, data)
