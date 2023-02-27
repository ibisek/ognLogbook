"""
DDB = Device DataBase
Maintains DDB and adds & stores newly discovered records into db.
"""

from configuration import dbConnectionInfo
from db.DbSource import DbSource
from db.DbThread import DbThread
from singleton import Singleton


class DDBRecord:
    def __init__(self):
        self.id = 0
        self.device_type = None  # O/F/I
        self.device_id = None  # tracker id
        self.aircraft_type = None  # default 0
        self.aircraft_registration = None
        self.aircraft_cn = None
        self.tracked = True
        self.identified = True

        self.dirty = True  # auxiliary flag; indicates whether in sync with db

    @staticmethod
    def fromDbRow(row):
        rec = DDBRecord()

        (rec.id, rec.device_type, rec.device_id,
         rec.aircraft_type, rec.aircraft_registration, rec.aircraft_cn,
         rec.tracked, rec.identified) = row

        rec.dirty = False

        return rec

    """
    @returns device_type + device_id; e.g. I123456; useful as unique key
    """

    def getCombinedDeviceAddress(self) -> str:
        return f"{self.device_type}{self.device_id}"


class DDB:  # ..extends (Singleton)
    CRON_INTERVAL = 5 * 60  # [s]

    _instance = None
    records = {}

    def __init__(self):
        """
        !DO NOT USE! Use getInstance() instead!
        """
        super(DDB, self).__init__()
        self._loadFromDb()

        self.dbThread = DbThread(dbConnectionInfo)
        self.dbThread.start()

    @staticmethod
    def getInstance():
        if not DDB._instance:
            DDB._instance = DDB()

        return DDB._instance

    def stop(self):
        self.dbThread.stop()

    def __del__(self):
        self.stop()

    def _loadFromDb(self):
        self.records.clear()

        sql = "SELECT * FROM ddb;"
        with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            for row in rows:
                ddbRec = DDBRecord.fromDbRow(row)
                self.records[ddbRec.getCombinedDeviceAddress()] = ddbRec

    def insert(self, rec: DDBRecord) -> bool:
        key = rec.getCombinedDeviceAddress()
        if key not in self.records:
            self.records[key] = rec
            return True

        return False

    def exists(self, device_type: str, device_id: str) -> bool:
        """
        :param device_type: O/I/F..
        :param device_id: device address
        """
        key = f"{device_type}{device_id}"
        return key in self.records

    def get(self, device_type: str, device_id: str) -> DDBRecord:
        """
        :param device_type: O/I/F..
        :param device_id: device address
        """
        key = f"{device_type}{device_id}"
        return self.records.get(key, None)

    def _syncToDb(self):
        dirtyRecords = [rec for rec in self.records.values() if rec.dirty]

        for rec in dirtyRecords:
            if not rec.device_type or not rec.device_id or not rec.aircraft_registration:
                continue  # no point of inserting into db

            aircraftType = rec.aircraft_type if rec.aircraft_type else 0
            aircraftCn = rec.aircraft_cn if rec.aircraft_cn else ''
            tracked = 'true' if rec.tracked else 'false'
            identified = 'true' if rec.identified else 'false'

            if rec.id:
                sql = f"UPDATE ddb " \
                      f"SET (device_type='{rec.device_type}', device_id='{rec.device_id}', " \
                      f"aircraft_type='{aircraftType}', aircraft_registration='{rec.aircraft_registration}', aircraft_cn='{aircraftCn}', " \
                      f"tracked={tracked}, identified={identified}) " \
                      f"WHERE id = {rec.id};"
                self.dbThread.addStatement(sql)

            else:
                sql = f"INSERT INTO ddb " \
                      f"(device_type, device_id, aircraft_type, aircraft_registration, aircraft_cn, tracked, identified) " \
                      f"VALUES " \
                      f"('{rec.device_type}', '{rec.device_id}', {aircraftType}, '{rec.aircraft_registration}', '{aircraftCn}', " \
                      f"{tracked}, {identified});"
                self.dbThread.addStatement(sql)

            rec.dirty = False

    def cron(self):
        self._syncToDb()
        self._loadFromDb()


if __name__ == '__main__':
    ddb = DDB.getInstance()
    print("ddb size:", len(ddb.records))

    rec = DDBRecord()
    rec.device_type = 'X'
    rec.device_id = "123456"
    rec.aircraft_registration = 'OK-XXX'
    res = ddb.insert(rec)
    print("insert res1:", res)

    exists = ddb.exists(rec.device_type, rec.device_id)
    print("exists:", exists)

    res = ddb.insert(rec)
    print("insert res2:", res)

    # rec2 = ddb.get('O', 'C35001')
    # rec2.aircraft_registration = "zmeneno"
    # rec2.dirty = True
    # print(rec2)

    ddb.syncToDb()

    print('KOHEU.')
