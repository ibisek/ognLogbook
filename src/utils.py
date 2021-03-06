from datetime import datetime, time, timedelta


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


def getDayTimestamps(forDay: datetime = None):
    """
    :param forDay use None for today
    :return: start, end timestamps of current day
    """
    if not forDay:
        # forDay = datetime.today()
        return None, None

    startTs = datetime.combine(forDay, time.min).timestamp()
    endTs = datetime.combine(forDay, time.max).timestamp()

    return int(startTs), int(endTs)


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


def getGroundSpeedThreshold(aircraftType: int, forEvent: str):
    """
    :param aircraftType:
    :param forEvent: 'L' / 'T' threshold for expected event
    :return:
    """
    # define AIRCRAFT_TYPE_UNKNOWN 0
    # define AIRCRAFT_TYPE_GLIDER 1
    # define AIRCRAFT_TYPE_TOW_PLANE 2
    # define AIRCRAFT_TYPE_HELICOPTER_ROTORCRAFT 3
    # define AIRCRAFT_TYPE_PARACHUTE 4
    # define AIRCRAFT_TYPE_DROP_PLANE 5
    # define AIRCRAFT_TYPE_HANG_GLIDER 6
    # define AIRCRAFT_TYPE_PARA_GLIDER 7
    # define AIRCRAFT_TYPE_POWERED_AIRCRAFT 8
    # define AIRCRAFT_TYPE_JET_AIRCRAFT 9
    # define AIRCRAFT_TYPE_UFO 10
    # define AIRCRAFT_TYPE_BALLOON 11
    # define AIRCRAFT_TYPE_AIRSHIP 12
    # define AIRCRAFT_TYPE_UAV 13
    # define AIRCRAFT_TYPE_STATIC_OBJECT 15
    # define AIRCRAFT_TYPE_WRONG 16 // a placeholder to identify mangled packets

    if forEvent == 'L':
        if aircraftType in [1, 3, 4, 6, 7, 11, 12, 13, 15]:
            return 20   # [km/h] glider
        else:
            return 50   # [km/h] tow

    else:   # takeoff threshold
        return 80  # [km/h] all


def formatTsToHHMM(ts: datetime):
    """
    Formats ts rounded HH:MM.
    To be used in tepmlates in form {{ formatTsHHMM(ts) }}
    """
    if ts:
        hour = ts.hour
        min = ts.minute
        sec = ts.second

        if sec >= 30:
            min += 1
            if min > 59:
                min = 0
                hour += 1
                if hour > 23:
                    hour = 0

        return f"{hour}:{min:02d}"

    else:
        return '?'
