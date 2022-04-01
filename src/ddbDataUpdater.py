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
from pymysql.cursors import Cursor

DDB_URL = 'https://ddb.glidernet.org/download/'
FLARMNET_URL = 'https://www.flarmnet.org/static/files/wfn/data.fln'


# def _dropAllDdbRecords():
#     with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
#         cur.execute("DELETE FROM ddb;")

def _insertOrAmendRecord(cursor: Cursor,
                         deviceType: str, deviceId: str,
                         aircraftType: str, registration: str, cn: str,
                         tracked: bool = True, identified: bool = True,
                         updateRecordIfExists: bool = True):
    # MYSQL:
    # strSql = f"INSERT INTO ddb " \
    #          f"(device_type, device_id, aircraft_type, aircraft_registration, aircraft_cn, tracked, identified)" \
    #          f"VALUES " \
    #          f"(%(device_type)s, %(device_id)s, %(aircraft_type)s, %(aircraft_registration)s, %(aircraft_cn)s, %(tracked)s, %(identified)s);"
    #
    # data = dict()
    # data['device_type'] = deviceType
    # data['device_id'] = deviceId
    # data['aircraft_type'] = aircraftType
    # data['aircraft_registration'] = registration
    # data['aircraft_cn'] = cn
    # data['tracked'] = tracked
    # data['identified'] = identified
    #
    # with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
    #     cur.execute(strSql, data)

    # SQLITE:
    select = f"SELECT id, device_type, device_id, aircraft_type, aircraft_registration, aircraft_cn, tracked, identified FROM ddb WHERE device_id='{deviceId}' limit 1;"

    res = cursor.execute(select)
    if res:
        if not updateRecordIfExists:
            return

        (id1, devType1, devId1, aircraftType1, registration1, cn1, tracked1,
         identified1) = cursor.fetchone()  # (id, 'F', '000000', 'HPH 304CZ-17', 'OK-7777', 'KN', 1, 1)
        if devType1 != deviceType or aircraftType1 != aircraftType or registration1 != registration1 or cn1 != cn or tracked1 != tracked or identified1 != identified:
            update = f"UPDATE ddb SET device_type = '{deviceType}', aircraft_type='{aircraftType}', aircraft_registration='{registration}', " \
                     f"aircraft_cn='{cn}', tracked={tracked}, identified={identified} " \
                     f"WHERE id = {id1};"
            cursor.execute(update)

    else:
        insert = f"INSERT INTO ddb " \
                 f"(device_type, device_id, aircraft_type, aircraft_registration, aircraft_cn, tracked, identified)" \
                 f"VALUES " \
                 f"('{deviceType}', '{deviceId}', '{aircraftType}', '{registration}', '{cn}', " \
                 f"{tracked}, {identified});"

        cursor.execute(insert)


def _downloadDataFile(url: str):
    print(f"Downloading data from {url}")
    resp = requests.get(url)

    if resp.status_code != 200:
        print(f"[WARN] Download of the datafile failed with code {resp.status_code}")
        sys.exit(1)

    return resp.text.split('\n')


def _processDDB():
    lines = _downloadDataFile(DDB_URL)
    if len(lines) < 10000:
        sys.exit(1)

    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:

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

            _insertOrAmendRecord(cursor=cur,
                                 deviceType=deviceType, deviceId=deviceId,
                                 aircraftType=aircraftType, registration=registration, cn=cn,
                                 tracked=tracked, identified=identified,
                                 updateRecordIfExists=True)


def _processFlarmnet():
    lines = _downloadDataFile(FLARMNET_URL)
    if len(lines) < 10000:
        sys.exit(1)

    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:

        for line in lines:
            if len(line) != 172:
                continue

            s = ""
            for i in range(0, len(line), 2):
                s += chr(int(line[i:i+2], 16))

            deviceType = 'F'
            deviceId = s[0:27].strip()  # xxyyzz
            registration = s[27:48].strip()
            aircraftType = s[48:69].strip()
            cn = s[76:79].strip()
            tracked = True
            identified = True

            if len(registration) > 8:   # 8 is column limit; apparently some mistaken value
                continue

            _insertOrAmendRecord(cursor=cur,
                                 deviceType=deviceType, deviceId=deviceId,
                                 aircraftType=aircraftType, registration=registration, cn=cn,
                                 tracked=tracked, identified=identified,
                                 updateRecordIfExists=False)  # do not overwrite OFN DDB records


if __name__ == '__main__':
    _processDDB()
    _processFlarmnet()
