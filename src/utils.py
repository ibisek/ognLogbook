from datetime import datetime, time, timedelta

from configuration import SPEED_THRESHOLD_GLIDER, SPEED_THRESHOLD_TOW


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
        # forDay = datetime.today()
        return None, None

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


def getGroundSpeedThreshold(aircraftType: int):
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

    if aircraftType in [1, 3, 4, 6, 7, 11, 12, 13, 15]:
        return 20   # [km/h] glider
    else:
        return 40   # [km/h] tow
