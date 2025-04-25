from datetime import datetime

from configuration import dbConnectionInfo
from db.DbSource import DbSource


def logIgcDownload(userId: str, recType: str, recId: int, remoteAddr: str):
    """
    :param userId:
    :param recType: 'f' for flight (tab. logbook_entries) or 't' for take-off (tab. logbook_events)
    :param recId:
    :param remoteAddr: remote IP address
    :return:
    """

    if recType not in ('f', 't'):
        return

    ts = round(datetime.utcnow().timestamp())

    strSql = f"INSERT INTO log_igc_download (ts, user_id, rec_type, rec_id, remote_addr) VALUES ({ts}, {userId}, '{recType}', {recId}, '{remoteAddr}');"
    print(f"strSql: {strSql}")

    with DbSource(dbConnectionInfo).getConnection().cursor() as c:
        c.execute(strSql)
