from datetime import datetime

from utils import formatDuration


def formatMailNotification(event, watcher):
    # TODO watcher.lang
    eventStr = 'start z' if event.event == 'T' else 'pristani v'
    dateTimeStr = 'Datum a cas'
    trackingStr = 'Trackovani letu dostupne z'
    flightRecordStr = 'Detaily a zaznam letu dostupne na'
    flightTimeStr = 'Zaznamenana doba letu'
    takeoffLocationStr = 'Detekovane misto vzletu'
    landingLocationStr = 'Detekovane misto pristani'
    footerStr = '\nToto je automaticky generovana zprava z https://logbook.ibisek.com.\nZrusit ci upravit nastaveni zasilani notifikaci lze ve sprave uctu na https://my.logbook.ibisek.com.'

    subject = f"{watcher.aircraft_registration} ({watcher.aircraft_cn}): {eventStr} {event.icaoLocation}"

    dt = datetime.fromtimestamp(event.ts)
    dtStr = datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")

    if event.event == 'T':  # take-off
        body = f"{dateTimeStr}: {dtStr}\n\n" \
               f"{trackingStr} https://logbook.ibisek.com/loc/{event.icaoLocation}\n" \
               f"\n{landingLocationStr}:\n\tlat: {event.lat:.4f}\n\tlon: {event.lon:.4f}\n"\

    else:   # landing
        body = f"{dateTimeStr}: {dtStr}\n"
        if event.flightTime > 0:
            body += f"\n{flightTimeStr}: {formatDuration(event.flightTime)}\n"
        body += f"\n{flightRecordStr} https://logbook.ibisek.com/loc/{event.icaoLocation}\n"
        body += f"\n{landingLocationStr}:\n\tlat: {event.lat:.4f}\n\tlon: {event.lon:.4f}\n"

    body += footerStr

    return subject, body
