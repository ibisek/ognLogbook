from datetime import datetime

from translations import gettext
from utils import formatDuration


def formatMailNotification(event, watcher):
    lang = watcher.lang
    eventStr = gettext('notif.mail.departure', lang) if event.event == 'T' else gettext('notif.mail.landing', lang)
    dateTimeStr = gettext('notif.mail.datetime', lang)
    trackingStr = gettext('notif.mail.flightTracking', lang)
    flightRecordStr = gettext('notif.mail.flightDetails', lang)
    flightTimeStr = gettext('notif.mail.flightTime', lang)
    takeoffLocationStr = gettext('notif.mail.detectedTakoffLoc', lang)
    landingLocationStr = gettext('notif.mail.detectedLandingLoc', lang)
    mapStr = gettext('notif.mail.map', lang)
    footerStr = gettext('notif.mail.footer', lang)

    mapUrlTemplate = "https://en.mapy.cz/zakladni?x={lon:.5f}&y={lat:.5f}&z=16&base=ophoto&source=coor&id={lon:.5f}%2C{lat:.5f}"

    location = event.icaoLocation
    if not event.icaoLocation or event.icaoLocation == 'null':
        location = '(??)'
        event.icaoLocation = None

    subject = f"{watcher.aircraft_registration} ({watcher.aircraft_cn}) {eventStr} {location}"

    dt = datetime.fromtimestamp(event.ts)
    dtStr = datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")
    mapLink = mapUrlTemplate.format(lat=event.lat, lon=event.lon)

    if event.event == 'T':  # take-off
        body = f"{dateTimeStr}: {dtStr}\n\n"

        if event.icaoLocation:
            body += f"{trackingStr} https://logbook.ibisek.com/loc/{event.icaoLocation}\n"
        else:
            body += f"\n{takeoffLocationStr}:\n\tlat: {event.lat:.4f}\n\tlon: {event.lon:.4f}\n\t{mapStr}: {mapLink}\n"

    else:   # landing
        body = f"{dateTimeStr}: {dtStr}\n"

        if event.flightTime > 0:
            body += f"\n{flightTimeStr}: {formatDuration(event.flightTime)}\n"
            print(f"[TEMP] XXX ft: {event.flightTime}; formatted: {formatDuration(event.flightTime)}")

        if event.icaoLocation:
            body += f"\n{flightRecordStr} https://logbook.ibisek.com/loc/{event.icaoLocation}\n"
        else:
            body += f"\n{landingLocationStr}:\n\tlat: {event.lat:.4f}\n\tlon: {event.lon:.4f}\n\t{mapStr}: {mapLink}\n"

    body += '\n' + footerStr

    return subject, body
