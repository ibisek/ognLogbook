"""
Created on 20. 5. 2020

@author: ibisek
"""

import sys
import flask
import getopt
from datetime import datetime
from flask import request

from configuration import debugMode
from dao.logbookDao import listDepartures, listArrivals, listFlights, getSums
from dao.stats import getNumFlightsToday, getTotNumFlights, getLongestFlightTimeToday, getHighestTrafficToday
from utils import getDaysLinks, formatDuration
from translations import gettext

app = flask.Flask(__name__)
app.jinja_env.globals.update(gettext=gettext)


@app.route('/')
def index():
    langs = [al[0].lower() for al in request.accept_languages]
    icaoFilter = []
    if 'cz' in langs or 'cs' in langs or 'sk' in langs:
        icaoFilter.append('LK')
        icaoFilter.append('LZ')
    elif 'de' in langs:
        icaoFilter.append('LO')     # at
        icaoFilter.append('ED')     # de
        icaoFilter.append('LS')     # ch
    elif 'pl' in langs:
        icaoFilter.append('EP')
    if 'fi' in langs or 'se' in langs or 'no' in langs:
        icaoFilter.append('EF')     # fi
        icaoFilter.append('ES')     # se

    departures, arrivals, flights = _prepareData(limit=25, icaoFilter=icaoFilter, sortTsDesc=True)

    totNumFlights = getTotNumFlights()
    numFlightsToday = getNumFlightsToday()
    longestFlightTime = getLongestFlightTimeToday()
    highestTrafficLocation, highestTrafficCount = getHighestTrafficToday()

    return flask.render_template('index.html', debugMode=debugMode, date=datetime.now(),
                                 departures=departures, arrivals=arrivals, flights=flights,
                                 numFlightsToday=numFlightsToday, totNumFlights=totNumFlights,
                                 longestFlightTime=longestFlightTime, highestTrafficLocation=highestTrafficLocation,
                                 highestTrafficCount=highestTrafficCount)


@app.route('/loc/<icaoCode>', methods=['GET'])
@app.route('/loc/<icaoCode>/<date>', methods=['GET'])
def filterByIcaoCode(icaoCode, date=None):
    if icaoCode:
        icaoCode = _saninitise(icaoCode)

    if not icaoCode:
        return flask.redirect('/')

    if date:
        date = _saninitise(date)
        try:
            date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            date = datetime.now()
    else:
        date = datetime.now()

    departures, arrivals, flights = _prepareData(icaoCode=icaoCode, forDay=date)

    linkPrevDay, linkNextDay = getDaysLinks(f"/loc/{icaoCode}", date)

    return flask.render_template('index.html', debugMode=debugMode, date=date, icaoCode=icaoCode,
                                 linkPrevDay=linkPrevDay, linkNextDay=linkNextDay,
                                 departures=departures, arrivals=arrivals, flights=flights)


@app.route('/reg/<registration>', methods=['GET'])
@app.route('/reg/<registration>/<date>', methods=['GET'])
def filterByRegistration(registration, date=None):
    registration = _saninitise(registration)

    if not registration:
        return flask.redirect('/')

    if date:
        date = _saninitise(date)
        try:
            date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            date = datetime.now()
    else:
        date = datetime.now()

    linkPrevDay, linkNextDay = getDaysLinks(f"/reg/{registration}", date)
    numFlights, totalFlightTime = getSums(registration=registration, forDay=date)
    departures, arrivals, flights = _prepareData(registration=registration, forDay=date)

    totalFlightTime = formatDuration(totalFlightTime)

    return flask.render_template('index.html', debugMode=debugMode, date=date, registration=registration,
                                 linkPrevDay=linkPrevDay, linkNextDay=linkNextDay,
                                 numFlights=numFlights, totalFlightTime=totalFlightTime,
                                 departures=departures, arrivals=arrivals, flights=flights, showFlightsOnly=True)


def _prepareData(icaoCode=None, registration=None, forDay=None, limit=None, icaoFilter=[], sortTsDesc=False):

    if icaoCode:
        icaoCode = _saninitise(icaoCode)

    if registration:
        registration = _saninitise(registration)

    departures = listDepartures(icaoCode=icaoCode, registration=registration, forDay=forDay, limit=limit, icaoFilter=icaoFilter, sortTsDesc=sortTsDesc)
    arrivals = listArrivals(icaoCode=icaoCode, registration=registration, forDay=forDay, limit=limit, icaoFilter=icaoFilter, sortTsDesc=sortTsDesc)
    flights = listFlights(icaoCode=icaoCode, registration=registration, forDay=forDay, limit=limit, icaoFilter=icaoFilter, sortTsDesc=sortTsDesc)

    return departures, arrivals, flights


@app.route('/search/<text>', methods=['GET'])
def search(text=None):
    text = _saninitise(text)

    if len(text) == 4 and text.upper()[0:2] in ['EB', 'ED', 'EF', 'EH', 'EK', 'EP', 'ES',
                                                'LB', 'LH', 'LI', 'LJ', 'LK', 'LO', 'LS', 'LZ']:
        return flask.redirect(f"/loc/{text.upper()}")
    else:
        return flask.redirect(f"/reg/{text}")


@app.route('/csv/<icaoCode>/<date>', methods=['GET'])
def getCsv(icaoCode, date=None):
    if not icaoCode:
        return flask.redirect('/')

    if date:
        date = _saninitise(date)
        try:
            date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            date = datetime.now()
    else:
        date = datetime.now()

    icaoCode = _saninitise(icaoCode).upper()

    flights = listFlights(icaoCode=icaoCode, forDay=date, limit=100)
    csvText = _toFlightOfficeCsv(flights)

    output = flask.make_response(csvText)

    output.headers["Content-Disposition"] = f"attachment; filename={icaoCode}.csv"
    output.headers["Content-type"] = "text/csv"

    return output


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)  # method not allowed
@app.errorhandler(413)
def handle_error(error):
    return flask.render_template("error40x.html", code=error.code, message=error.description)


# @app.errorhandler(Exception)
# def unhandled_exception(error):
#     msg = "Unhandled Exception: {}".format(error)
#     # logger.error(msg)
#     # app.logger.error(msg)
#     return flask.render_template('error40x.html', code=500), 500


def _saninitise(s):
    return s.replace('\\', '').replace(';', '').replace('\'', '').replace('--', '').replace('"', '').strip()


def _toFlightOfficeCsv(flights: list):
    DEV_TYPES = {'F': 'flarm', 'O': 'ogn', 'I': 'icao'}

    rows = list()   # csv strings

    for flight in flights:
        idPrefix = DEV_TYPES[flight.device_type] if flight.device_type in DEV_TYPES else 'unknown'

        row = list()  # csv items
        row.append(flight.takeoff_dt.strftime('%Y-%m-%d'))  # date
        row.append(flight.takeoff_ts)    # SEQ_NR
        row.append(f"{idPrefix}:{flight.address}")    # ID
        row.append(flight.registration)    # CALLSIGN
        row.append(flight.cn)    # COMPETITION_NUMBER
        row.append(0)    # (aircraft?) TYPE
        row.append(flight.aircraft_type)    # DETAILED_TYPE
        row.append('')    # CREW1
        row.append('')    # CREW2
        row.append(flight.takeoff_dt.strftime('%H:%M:%S'))    # TKOF_TIME 12:34:56
        row.append(flight.takeoff_icao)    # TKOF_AP LKxx
        row.append('')    # TKOF_RWY
        row.append('')    # RESERVED
        row.append(flight.landing_dt.strftime('%H:%M:%S'))    # LDG_TIME 12:34:56
        row.append(flight.landing_icao)    # LDG_AP LKxx
        row.append('')    # LDG_RWY
        row.append('')    # LDG_TURN
        row.append('')    # MAX_ALT
        row.append('')    # AVERAGE_CLIMB_RATE
        row.append(str(flight.landing_dt - flight.takeoff_dt))    # FLIGHT_TIME
        row.append('')    # DAY_DIFFERENCE
        row.append('')    # LAUNCH_METHOD
        row.append('')    # INITIAL_CLIMBRATE
        row.append('')    # TOW_ID
        row.append('')    # TOW_CALLSIGN
        row.append('')    # TOW_COMPETITION_NUMBER
        row.append('')    # TOW_SEQUENCE_NUMBER

        line = ';'.join([str(i) for i in row])
        rows.append(line)

    lines = '\n'.join(rows)

    header = 'DATE;SEQ_NR;ID;CALLSIGN;COMPETITION_NUMBER;TYPE;DETAILED_TYPE;CREW1;CREW2;TKOF_TIME;TKOF_AP;TKOF_RWY;RESERVED;LDG_TIME;LDG_AP;LDG_RWY;LDG_TURN;MAX_ALT;AVERAGE_CLIMB_RATE;FLIGHT_TIME;DAY_DIFFERENCE;LAUNCH_METHOD;INITIAL_CLIMBRATE;TOW_ID;TOW_CALLSIGN;TOW_COMPETITION_NUMBER;TOW_SEQUENCE_NUMBER\n'

    return header + lines


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d")
        for optPair in opts:

            if optPair[0] == "-d":

                debugMode = True

    # handle invalid script arguments
    except getopt.GetoptError as e:

        # print error message to stderr
        print("Argument error: " + e.msg, file=sys.stderr)
        # exit application
        sys.exit(1)

    app.run(debug=debugMode)
