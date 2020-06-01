"""
{{ gettext('') }}
"""

from flask import request

i10n = dict()
i10n['main.departures'] = ['Departures', 'Odlety', 'Abflüge']
i10n['main.arrivals'] = ['Arrivals', 'Přílety', 'Ankünfte']
i10n['main.flights'] = ['Flights', 'Přelety', 'Überflüge']
i10n['tab.date'] = ['Date', 'Datum', 'Datum']
i10n['tab.time'] = ['Time', 'Čas', 'Zeit']
i10n['tab.loc'] = ['Loc', 'Místo', 'Ort']
i10n['tab.reg'] = ['Reg', 'Registrace', 'Kennz.']
i10n['tab.cn'] = ['CN', 'SZ', 'WK']
i10n['tab.acftType'] = ['Type', 'Typ', 'Flugzeugtyp']
i10n['tab.to'] = ['Take-off', 'Odlet', 'Abflug']
i10n['tab.land'] = ['Landing', 'Přílet', 'Landung']
i10n['tab.ft'] = ['Flight time', 'Doba letu', 'Flugzeit']

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

i10n['sum.flights'] = ['Flights', 'Letů', 'Anzahl der Flüge']
i10n['sum.hours'] = ['Hours', 'Hodin', 'Gesamtflugzeit']


i10n['werbung.vfrmanual'] = ['VFR Manual', 'VFR Manuál', 'VFR Manual']

i10n[''] = ['', '']


def gettext(key='x'):
    lan = request.accept_languages.best
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
