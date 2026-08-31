import logging
from datetime import datetime, timezone

from configuration import dbConnectionInfo
from db.DbSource import DbSource

log = logging.getLogger(__name__)


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

    if remoteAddr > 45:     # IPv6 / mapped IPv4 addresses might be up to 45 chars long
        log.warning(f"Excessively long remoteAddr: {remoteAddr}")

    ts = round(datetime.now(tz=timezone.utc).timestamp())

    strSql = f"INSERT INTO log_igc_download (ts, user_id, rec_type, rec_id, remote_addr) VALUES ({ts}, {userId}, '{recType}', {recId}, '{remoteAddr}');"

    with DbSource(dbConnectionInfo).getConnection().cursor() as c:
        c.execute(strSql)
