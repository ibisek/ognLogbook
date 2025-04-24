from datetime import datetime
import pytz
from tzfpy import get_tz


def formatDuration(seconds):
    if not seconds:
        return 0

    h = seconds // 3600
    s = seconds % 3600
    m = s // 60
    s = s % 60

    if s >= 30:
        if m == 59:
            h += 1
            m = 0
        else:
            m += 1

    if h > 0:
        dur = f"{h}\N{DEGREE SIGN} {m}'"
    else:
        dur = f"{m}'"

    return dur


def getLocalTzDate(utcTs: int, lat: float, lon: float) -> str:
    """
    @return local date in given timezone by location
    """
    dateLocal = None

    try:
        tzStr = get_tz(lon, lat)  # !! order LON , LAT !!
        tzInfo = pytz.timezone(tzStr)
        dtLocal = datetime.fromtimestamp(utcTs, tz=tzInfo)
        dateLocal = dtLocal.strftime('%Y-%m-%d')

    except pytz.exceptions.UnknownTimeZoneError as e:
        print(f"[ERROR] Unknown timezone for lat {lat:.4f} lon {lon:.4f}:", str(e))
        dateLocal = datetime.fromtimestamp(utcTs, tz=pytz.timezone('UTC'))

    return dateLocal
