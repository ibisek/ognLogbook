from datetime import datetime, time, timedelta


def formatDuration(seconds):
    h = seconds // 3600
    s = seconds % 3600
    m = s // 60
    s = s % 60

    if s > 30:
        if m == 59:
            h += 1
            m = 0
        else:
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


def getDaysLinks(baselink: str, date: datetime):
    """
    :param baselink:
    :param date:
    :return:
    """

    if not date:
        date = datetime.now()

    linkNextDay = None
    if date.date() < datetime.now().date():
        linkNextDay = "{}/{}".format(baselink, (date + timedelta(1)).strftime('%Y-%m-%d'))

    linkPrevDay = "{}/{}".format(baselink, (date - timedelta(1)).strftime('%Y-%m-%d'))

    return linkPrevDay, linkNextDay
