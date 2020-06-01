"""
{{ gettext('') }}
"""

from flask import request

i10n = dict()
i10n['main.departures'] = ['Departures', 'Odlety']
i10n['main.arrivals'] = ['Arrivals', 'Přílety']
i10n['main.flights'] = ['Flights', 'Přelety']
i10n['tab.date'] = ['Date', 'Datum']
i10n['tab.time'] = ['Time', 'Čas']
i10n['tab.loc'] = ['Loc', 'Místo']
i10n['tab.reg'] = ['Reg', 'Registrace']
i10n['tab.cn'] = ['CN', 'SZ']
i10n['tab.acftType'] = ['Type', 'Typ']
i10n['tab.to'] = ['Take-off', 'Odlet']
i10n['tab.land'] = ['Landing', 'Přílet']
i10n['tab.ft'] = ['Flight time', 'Doba letu']

i10n['stat.line1'] = ['Registered flights', 'Registrované lety']
i10n['stat.line2'] = ['Flights today', 'Letů dnes']
i10n['stat.line3'] = ['Longest flight', 'Nejdelší let']
i10n['stat.line4'] = ['Highest traffic', 'Největší provoz']
i10n['stat.line1.hint'] = ['Total number of registered flights since big bang', 'Celkový počet registrovaných letů (od počátku věků ;))']
i10n['stat.line2.hint'] = ['Number of flights registered today', 'Počet dnes nově zaregistrovaných letů']
i10n['stat.line3.hint'] = ['Longest time interval between take-off and landing', 'Délka nejdelšího letu']
i10n['stat.line4.hint'] = ['Location with the most dense traffic of the day (with number of take-offs + landings)', 'Letiště s největším provozem dne (s počtem vzletů + přistání)']
i10n['stat.none1'] = ['none', 'žádný']
i10n['stat.none2'] = ['none', 'není']

i10n['search.hint'] = ['ICAO code or registration', 'ICAO kód nebo registrace']

i10n['sum.flights'] = ['Flights', 'Letů']
i10n['sum.hours'] = ['Hours', 'Hodin']

i10n['werbung.vfrmanual'] = ['VFR Manual', 'VFR Manuál']

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
    else:
        return i10n[key][0]
