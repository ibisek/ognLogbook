from configuration import dbConnectionInfo
from db.DbSource import DbSource


class PermanentStorage:

    def __init__(self, addressType: str):
        self.addressType = addressType
        self.entries = set()

    def reload(self):
        strSql = f"SELECT addr FROM permanent_storage WHERE addr_type='{self.addressType}' AND active=true"
        with DbSource(dbConnectionInfo).getConnection().cursor() as c:
            c.execute(strSql)
            while row := c.fetchone():
                address = row[0]
                self.entries.add(address)

    def eligible4ps(self, address) -> bool:
        """
        Is specified address' data eligible for permanent storage?
        :param address:
        :return:
        """
        return address in self.entries


class PermanentStorageFactory:
    permanentStorages = {}

    @staticmethod
    def storageFor(addressType: str) -> PermanentStorage:
        """
        :param addressType: char O=OGN, I=ICAO, F=Flarm, ..
        """
        ps = PermanentStorageFactory.permanentStorages.get(addressType)
        if not ps:
            ps = PermanentStorage(addressType=addressType)
            ps.reload()
            PermanentStorageFactory.permanentStorages[addressType] = ps

        return ps


if __name__ == '__main__':
    ps = PermanentStorageFactory.storageFor('O')
    res = ps.eligible4ps('C35001')
    print(f"RES1: {res}")

    ps = PermanentStorageFactory.storageFor('I')
    res = ps.eligible4ps('C35001')
    print(f"RES2: {res}")
