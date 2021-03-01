"""
Created on 20. 5. 2020

@author: ibisek
"""

import sys
import math
import flask
import getopt
from platform import node
from datetime import datetime, timedelta
from flask import request
from collections import namedtuple

from configuration import DEBUG, MAX_DAYS_IN_RANGE
from airfieldManager import AirfieldManager, AirfieldRecord
from dao.logbookDao import listDepartures, listArrivals, listFlights, getSums
from dao.stats import getNumFlightsToday, getTotNumFlights, getLongestFlightTimeToday, getHighestTrafficToday
from utils import getDaysLinks, formatDuration, formatTsToHHMM
from translations import gettext

app = flask.Flask(__name__)
app.jinja_env.globals.update(gettext=gettext)
app.jinja_env.globals.update(formatTsToHHMM=formatTsToHHMM)
app.jinja_env.globals.update(node=node)

DayRecord = namedtuple('DayRecords', ['date', 'numFlights', 'totalFlightTime', 'departures', 'arrivals', 'flights'])

afCountryCodes = AirfieldManager().afCountryCodes


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

    departures, arrivals, flights = _prepareData(limit=25, icaoFilter=icaoFilter, sortTsDesc=True, orderByCol='landing_ts')

    dayRecord: DayRecord = DayRecord(date=None, numFlights=None, totalFlightTime=None,
                                     departures=departures, arrivals=arrivals, flights=flights)

    totNumFlights = getTotNumFlights()
    numFlightsToday = getNumFlightsToday()
    longestFlightTime = getLongestFlightTimeToday()
    highestTrafficLocation, highestTrafficCount = getHighestTrafficToday()

    return flask.render_template('index.html', debugMode=DEBUG, date=datetime.now(),
                                 dayRecords=[dayRecord],
                                 numFlightsToday=numFlightsToday, totNumFlights=totNumFlights,
                                 longestFlightTime=longestFlightTime, highestTrafficLocation=highestTrafficLocation,
                                 highestTrafficCount=highestTrafficCount)


@app.route('/loc/<icaoCode>', methods=['GET'])
@app.route('/loc/<icaoCode>/<date>', methods=['GET'])
@app.route('/loc/<icaoCode>/<date>/<dateTo>', methods=['GET'])
def filterByIcaoCode(icaoCode, date=None, dateTo=None):
    if icaoCode:
        icaoCode = _saninitise(icaoCode)

    if not icaoCode:
        return flask.redirect('/')

    date = _parseDate(date)
    dateTo = _parseDate(dateTo) if dateTo else None
    dateNow = datetime.now()
    if dateTo:
        if dateTo > dateNow:
            dateTo = dateNow

        # set last second of the day:
        dateTo += timedelta(hours=23, minutes=59, seconds=59)

    numDays = round((dateTo.timestamp() - date.timestamp()) / 86400) if dateTo else 1   # timedelta.seconds doesn't work correctly
    if numDays > MAX_DAYS_IN_RANGE:
        numDays = MAX_DAYS_IN_RANGE

    linkPrevDay, linkNextDay = getDaysLinks(f"/loc/{icaoCode}", date)

    dayRecords = []
    for i in range(numDays):
        currentDate = date + timedelta(days=i)

        departures, arrivals, flights = _prepareData(icaoCode=icaoCode, forDay=currentDate)

        dayRecord: DayRecord = DayRecord(date=currentDate, numFlights=None, totalFlightTime=None,
                                         departures=departures, arrivals=arrivals, flights=flights)

        if len(departures) > 0 or len(arrivals) > 0 or len(flights) > 0:
            dayRecords.append(dayRecord)

    # This reloads the entire file every time the page is refreshed (!) However, perhaps still faster then querying and maintaining the DB.
    try:
        _, airfieldsDict = AirfieldManager.loadAirfieldsFromFile()
        ar: AirfieldRecord = airfieldsDict[icaoCode]
        lat, lon = math.degrees(ar.lat), math.degrees(ar.lon)

        return flask.render_template('index.html', debugMode=DEBUG, date=date, icaoCode=icaoCode,
                                     linkPrevDay=linkPrevDay, linkNextDay=linkNextDay,
                                     dayRecords=dayRecords,
                                     lat=lat, lon=lon)

    except KeyError as e:
        return flask.redirect('/')


@app.route('/reg/<registration>', methods=['GET'])
@app.route('/reg/<registration>/<date>', methods=['GET'])
@app.route('/reg/<registration>/<date>/<dateTo>', methods=['GET'])
def filterByRegistration(registration, date=None, dateTo=None):
    registration = _saninitise(registration)

    if not registration:
        return flask.redirect('/')

    date = _parseDate(date)
    dateTo = _parseDate(dateTo) if dateTo else None

    dateNow = datetime.now()
    if dateTo:
        if dateTo > dateNow:
            dateTo = dateNow

        # set last second of the day:
        dateTo += timedelta(hours=23, minutes=59, seconds=59)

    numDays = round((dateTo.timestamp() - date.timestamp()) / 86400) if dateTo else 1  # timedelta.seconds doesn't work correctly
    if numDays > MAX_DAYS_IN_RANGE:
        numDays = MAX_DAYS_IN_RANGE

    linkPrevDay, linkNextDay = getDaysLinks(f"/reg/{registration}", date)

    dayRecords = []
    for i in range(numDays):
        currentDate = date + timedelta(days=i)

        numFlights, totalFlightTime = getSums(registration=registration, forDay=currentDate)
        totalFlightTime = formatDuration(totalFlightTime)
        departures, arrivals, flights = _prepareData(registration=registration, forDay=currentDate)

        dayRecord: DayRecord = DayRecord(date=currentDate, numFlights=numFlights, totalFlightTime=totalFlightTime,
                                         departures=departures, arrivals=arrivals, flights=flights)
        if numFlights > 0:
            dayRecords.append(dayRecord)

    return flask.render_template('index.html', debugMode=DEBUG, date=date, registration=registration,
                                 linkPrevDay=linkPrevDay, linkNextDay=linkNextDay,
                                 dayRecords=dayRecords,
                                 showFlightsOnly=True)


def _prepareData(icaoCode=None, registration=None, forDay=None, limit=None, icaoFilter=[], sortTsDesc=False, orderByCol='takeoff_ts'):

    if icaoCode:
        icaoCode = _saninitise(icaoCode)

    if registration:
        registration = _saninitise(registration)

    departures = listDepartures(icaoCode=icaoCode, registration=registration, forDay=forDay, limit=limit, icaoFilter=icaoFilter, sortTsDesc=sortTsDesc)
    arrivals = listArrivals(icaoCode=icaoCode, registration=registration, forDay=forDay, limit=limit, icaoFilter=icaoFilter, sortTsDesc=sortTsDesc)
    flights = listFlights(icaoCode=icaoCode, registration=registration, forDay=forDay, limit=limit, icaoFilter=icaoFilter,
                          sortTsDesc=sortTsDesc, orderByCol=orderByCol)

    return departures, arrivals, flights


@app.route('/search/<text>', methods=['GET'])
def search(text=None):
    text = _saninitise(text)

    # TODO determine if that is an ICAO code or registration!

    if len(text) == 4 and text.upper()[0:2] in afCountryCodes:
        return flask.redirect(f"/loc/{text.upper()}")
    else:
        return flask.redirect(f"/reg/{text}")


@app.route('/csv/<icaoCode>', methods=['GET'])
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

    output.headers["Content-Disposition"] = f"attachment; filename={icaoCode}_{date.strftime('%Y-%m-%d')}.csv"
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

def _parseDate(date: str):
    """
    :param date: parsed date or current date in case of wrong format or None
    :return:
    """
    if date:
        date = _saninitise(date)
        try:
            date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            date = datetime.now()
    else:
        date = datetime.now()

    return date


def _saninitise(s):
    return s.replace('\\', '').replace(';', '').replace('\'', '').replace('--', '').replace('"', '').strip()


def _formatRegistration(reg: str):
    if not reg:
        return reg

    reg = reg.upper()
    if '-' not in reg:
        if reg.startswith('OK') or reg.startswith('OM'):
            r = reg[0:2]
            s = reg[2:]
            reg = f"{r}-{s}"

        elif reg.startswith('D') or reg.startswith('F'):
            r = reg[0]
            s = reg[1:]
            reg = f"{r}-{s}"

    return reg


def _toFlightOfficeCsv(flights: list):
    DEV_TYPES = {'F': 'flarm', 'O': 'ogn', 'I': 'icao'}

    rows = list()   # csv strings

    for flight in flights:
        idPrefix = DEV_TYPES[flight.device_type] if flight.device_type in DEV_TYPES else 'unknown'

        registration = flight.registration if flight.registration else ''
        registration = _formatRegistration(registration)

        row = list()  # csv items
        row.append(flight.takeoff_dt.strftime('%Y-%m-%d'))  # date
        row.append(flight.id)    # SEQ_NR
        row.append(f"{idPrefix}")    # ID   :{flight.address}
        row.append(registration)    # CALLSIGN
        row.append(flight.cn if flight.cn else '')    # COMPETITION_NUMBER
        row.append(0)    # (aircraft?) TYPE
        row.append(flight.aircraft_type if flight.aircraft_type else '')    # DETAILED_TYPE
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
        row.append(flight.tow_id if flight.tow_id else '')    # TOW_ID
        row.append('')    # TOW_CALLSIGN
        row.append('')    # TOW_COMPETITION_NUMBER
        row.append('')    # TOW_SEQUENCE_NUMBER

        line = ','.join([str(i) for i in row])
        rows.append(line)

    lines = '\n'.join(rows)

    header = 'DATE,SEQ_NR,ID,CALLSIGN,COMPETITION_NUMBER,TYPE,DETAILED_TYPE,CREW1,CREW2,TKOF_TIME,TKOF_AP,TKOF_RWY,RESERVED,LDG_TIME,LDG_AP,LDG_RWY,LDG_TURN,MAX_ALT,AVERAGE_CLIMB_RATE,FLIGHT_TIME,DAY_DIFFERENCE,LAUNCH_METHOD,INITIAL_CLIMBRATE,TOW_ID,TOW_CALLSIGN,TOW_COMPETITION_NUMBER,TOW_SEQUENCE_NUMBER\n'

    return header + lines


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d")
        for optPair in opts:

            if optPair[0] == "-d":

                DEBUG = True

    # handle invalid script arguments
    except getopt.GetoptError as e:

        # print error message to stderr
        print("Argument error: " + e.msg, file=sys.stderr)
        # exit application
        sys.exit(1)

    if DEBUG:
        app.config['TEMPLATES_AUTO_RELOAD'] = True

    app.run(debug=DEBUG)
