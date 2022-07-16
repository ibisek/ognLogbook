# -*- coding: utf-8 -*-
"""
{{ gettext('') }}
"""

from flask import request

i10n = dict()
i10n['main.departures'] = ['Departures', 'Odlety', 'Abflüge']
i10n['main.arrivals'] = ['Arrivals', 'Přílety', 'Ankünfte']
i10n['main.flights'] = ['Flights', 'Lety', 'Überflüge']
i10n['main.map'] = ['(map)', '(mapa)', '(Karte)']
i10n['tab.date'] = ['Date', 'Datum', 'Datum']
i10n['tab.time'] = ['Time', 'Čas', 'Zeit']
i10n['tab.loc'] = ['Loc', 'Místo', 'Ort']
i10n['tab.reg'] = ['Reg', 'Registrace', 'Kennz.']
i10n['tab.cn'] = ['CN', 'SZ', 'WK']
i10n['tab.acftType'] = ['Type', 'Typ', 'Flugzeugtyp']
i10n['tab.to'] = ['Take-off', 'Odlet', 'Abflug']
i10n['tab.land'] = ['Landing', 'Přílet', 'Landung']
i10n['tab.ft'] = ['Flight time', 'Doba letu', 'Flugzeit']
i10n['tab.hidden'] = ['(hidden)', '(skrytá)', '(versteckt)']

i10n['stat.line1'] = ['Registered flights', 'Registrované lety', 'Registrierte Flüge']
i10n['stat.line2'] = ['Flights today', 'Letů dnes', 'Flüge heute']
i10n['stat.line3'] = ['Longest flight', 'Nejdelší let', 'Längster Flug']
i10n['stat.line4'] = ['Highest traffic', 'Největší provoz', 'Höchster Verkehr']
i10n['stat.line1.hint'] = ['Total number of registered flights since big bang', 'Celkový počet registrovaných letů (od počátku věků ;))', 'Alle registrierte Flüge seit immer ;)']
i10n['stat.line2.hint'] = ['Number of flights registered today', 'Počet dnes nově zaregistrovaných letů', 'Anzahl der heute registrierten Flüge']
i10n['stat.line3.hint'] = ['Longest time interval between take-off and landing', 'Délka nejdelšího letu', 'Die Länge des längsten Fluges heute']
i10n['stat.line4.hint'] = ['Location with the most dense traffic of the day (with number of take-offs + landings)', 'Letiště s největším provozem dne (s počtem vzletů + přistání)', 'Flughafen mit dem größten Verkehr des Tages (mit der Anzahl der Starts + Landungen)']
i10n['stat.none1'] = ['none', 'žádný', 'keiner']
i10n['stat.none2'] = ['none', 'není', 'keiner']

i10n['search.hint'] = ['ICAO code or registration', 'ICAO kód nebo registrace', 'ICAO-Code oder Registrierung']
i10n['search.notFound'] = ['No records have been found, recorded or we just don\'t know :P', 'Nic jsme nenašli, nezaznamenali, nebo prostě nevíme :P', 'Wir haben nichts gefunden, nichts bemerkt oder wir wissen einfach nicht :P']
i10n['search.notFound.short'] = ['no data', 'nejsou data', 'keine daten']

i10n['sum.flights'] = ['Flights', 'Letů', 'Anzahl der Flüge']
i10n['sum.hours'] = ['Hours', 'Hodin', 'Gesamtflugzeit']

i10n['werbung.vfrmanual'] = ['VFR Manual', 'VFR Manuál', 'VFR Manual']
i10n['werbung.krt2bt.link'] = ['https://ogn.ibisek.com/index.php/2022/04/20/krt2-bluetooth-adapter/', 'https://ogn.ibisek.com/index.php/en/2022/04/20/krt2-bluetooth/', 'https://ogn.ibisek.com/index.php/2022/04/20/krt2-bluetooth-adapter/']

i10n['notif.mail.departure'] = ['departed from', 'odstartoval z', 'gestartet von']
i10n['notif.mail.landing'] = ['landed at', 'přistál v', 'gelandet bei']
i10n['notif.mail.datetime'] = ['Date and time', 'Datum a čas', 'Datum und Zeit']
i10n['notif.mail.flightTracking'] = ['Flight tracking available at', 'Trackování letu dostupné z', 'Flugverfolgung verfügbar unter']
i10n['notif.mail.flightDetails'] = ['Flight details available at', 'Detaily a záznam letu dostupné na', 'Flugdetails verfügbar unter']
i10n['notif.mail.flightTime'] = ['Recorded flight-time', 'Zaznamenaná doba letu', 'Flugzeit']
i10n['notif.mail.detectedTakoffLoc'] = ['Detected take-off location', 'Detekovaní míisto vzletu', 'Startort']
i10n['notif.mail.detectedLandingLoc'] = ['Detected landing location', 'Detekované místo přistání', 'Landeplatz']
i10n['notif.mail.map'] = ['map', 'mapa', 'Karte']
i10n['notif.mail.footer'] = ['This is an automatically generated message by https://logbook.ibisek.com.\nYou can cancel or amend notification settings in your account at https://my.logbook.ibisek.com.',
                             'Toto je automaticky generovaná zpráva z https://logbook.ibisek.com.\nZrušit či upravit nastavení zasílaní notifikací lze ve správě účtu na adrese https://my.logbook.ibisek.com.',
                             'Dies ist eine automatisch generierte Nachricht von https://logbook.ibisek.com\nSie können die Benachrichtigungseinstellungen in Ihrem Konto unter https://my.logbook.ibisek.com ändern oder stornieren.']

i10n[''] = ['', '', '']


def gettext(key='x', lan=None):
    if not lan:
        try:
            lan = request.accept_languages.best
        except RuntimeError:
            lan = 'en'

    if not lan:
        return i10n[key][0]

    if 'cz' in lan:
        return i10n[key][1]
    elif 'cs' in lan:
        return i10n[key][1]
    elif 'sk' in lan:
        return i10n[key][1]
    elif 'en' in lan:
        return i10n[key][0]
    elif 'de' in lan:
        return i10n[key][2]
    else:
        return i10n[key][0]
