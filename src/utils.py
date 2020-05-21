
from datetime import datetime, time


def formatDuration(seconds):
    h = seconds % 3600
    s = seconds - h * 3600
    m = s % 60
    s = s - m * 60

    if s > 30:
        m += 1

    if h > 0:
        dur = f"{h}\N{DEGREE SIGN}{m}'"
    else:
        dur = f"{m}'"

    return dur


def getDayTimestamps(forDay: datetime = None):
    """
    :param forDay use None for today
    :return: start, end timestamps of current day
    """
    if not forDay:
        forDay = datetime.today()

    startTs = datetime.combine(forDay, time.min).timestamp()
    endTs = datetime.combine(forDay, time.max).timestamp()

    return startTs, endTs

