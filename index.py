"""
Created on 20. 5. 2020

@author: ibisek
"""
import json
import sys
import math
from datetime import datetime, timedelta
from collections import namedtuple

from distutils.log import Log
from flask import request, send_from_directory, session, jsonify
import flask
import getopt
from platform import node
import pytz

from configuration import DEBUG, MAX_DAYS_IN_RANGE, INFLUX_DB_HOST, INFLUX_DB_NAME, INFLUX_DB_NAME_PERMANENT_STORAGE
from airfieldManager import AirfieldManager, AirfieldRecord
from dataStructures import LogbookItem, addressPrefixes
from dao.logbookDao import listDepartures, listArrivals, listFlights, getSums, getFlight, getFlightIdForTakeoffId, getFlightInfoForTakeoff
from dao.permanentStorage import PermanentStorageFactory
from dao.stats import getNumFlightsToday, getTotNumFlights, getLongestFlightToday, getHighestTrafficToday
from db.InfluxDbThread import InfluxDbThread
from igc import flightToIGC

from utils import getDaysLinks, formatDuration, formatTsToHHMM, eligibleForMapView, saninitise, parseDate, limitDateRange
from translations import gettext

app = flask.Flask(__name__)
app.jinja_env.globals.update(gettext=gettext)
app.jinja_env.globals.update(formatTsToHHMM=formatTsToHHMM)
app.jinja_env.globals.update(node=node)
app.jinja_env.globals.update(eligibleForMapView=eligibleForMapView)

DayRecord = namedtuple('DayRecords', ['date', 'numFlights', 'totalFlightTime', 'departures', 'arrivals', 'flights'])

airfieldManager = AirfieldManager()
afCountryCodes = airfieldManager.afCountryCodes


@app.route('/set_timezone', methods=['POST'])
def set_timezone():
    """Receive timezone from the browser and store it in the session object."""
    timezone = request.data.decode('utf-8')
    session['browser_timezone'] = timezone
    session.modified = True
    return ''


def _getBrowserTimezone():
    # 1. get it from session:
    browser_timezone = session.get('browser_timezone')

    # 2. or get it from cookie:
    if not browser_timezone:
        browser_timezone = request.cookies.get('browser_timezone')
        # if browser_timezone:
        # session['browser_timezone'] = browser_timezone    # TODO XXX TOTO NEJEDE NA PRODUKCI!! KURWA PROC??
        # session.modified = True

    if browser_timezone:
        try:
            return pytz.timezone(browser_timezone)
        except pytz.UnknownTimeZoneError:
            return pytz.utc

    return pytz.utc


@app.route('/')
def index():
    # langs = [al[0].lower() for al in request.accept_languages]
    icaoFilter = []
    # if 'cz' in langs or 'cs' in langs or 'sk' in langs:
    #     icaoFilter.append('LK')
    #     icaoFilter.append('LZ')
    # elif 'de' in langs:
    #     icaoFilter.append('LO')     # at
    #     icaoFilter.append('ED')     # de
    #     icaoFilter.append('LS')     # ch
    # elif 'pl' in langs:
    #     icaoFilter.append('EP')
    # if 'fi' in langs or 'se' in langs or 'no' in langs:
    #     icaoFilter.append('EF')     # fi
    #     icaoFilter.append('ES')     # se

    display_tz = _getBrowserTimezone()

    departures, arrivals, flights = _prepareData(limit=25, icaoFilter=icaoFilter, sortTsDesc=True, orderByCol='landing_ts', display_tz=display_tz)

    dayRecord: DayRecord = DayRecord(date=None, numFlights=None, totalFlightTime=None,
                                     departures=departures, arrivals=arrivals, flights=flights)

    totNumFlights = getTotNumFlights()
    numFlightsToday = getNumFlightsToday()
    longestFlightId, longestFlightTime = getLongestFlightToday()
    highestTrafficLocation, highestTrafficCount = getHighestTrafficToday()

    return flask.render_template('index.html', debugMode=DEBUG, date=datetime.now(),
                                 dayRecords=[dayRecord],
                                 numFlightsToday=numFlightsToday, totNumFlights=totNumFlights,
                                 longestFlightTime=longestFlightTime, longestFlightId=longestFlightId,
                                 highestTrafficLocation=highestTrafficLocation,
                                 highestTrafficCount=highestTrafficCount)


@app.route('/loc/<icaoCode>', methods=['GET'])
@app.route('/loc/<icaoCode>/<date>', methods=['GET'])
@app.route('/loc/<icaoCode>/<date>/<dateTo>', methods=['GET'])
def filterByIcaoCode(icaoCode, date=None, dateTo=None):
    icaoCode = saninitise(icaoCode)
    if not icaoCode:
        return flask.redirect('/')

    date = parseDate(date, default=datetime.now())
    dateTo = parseDate(dateTo, default=None, endOfTheDay=True)
    if dateTo:
        dateNow = datetime.now()
        if dateTo > dateNow:
            dateTo = dateNow

    numDays = round((dateTo.timestamp() - date.timestamp()) / 86400) if dateTo else 1   # timedelta.seconds doesn't work correctly
    if numDays > MAX_DAYS_IN_RANGE:
        numDays = MAX_DAYS_IN_RANGE

    linkPrevDay, linkNextDay = getDaysLinks(f"/loc/{icaoCode}", date)

    display_tz = _getBrowserTimezone()
    dayRecords = []
    for i in range(numDays):
        currentDate = date + timedelta(days=i)

        departures, arrivals, flights = _prepareData(icaoCode=icaoCode, forDay=currentDate, display_tz=display_tz)

        dayRecord: DayRecord = DayRecord(date=currentDate, numFlights=None, totalFlightTime=None,
                                         departures=departures, arrivals=arrivals, flights=flights)

        if len(departures) > 0 or len(arrivals) > 0 or len(flights) > 0:
            dayRecords.append(dayRecord)

    # This reloads the entire file every time the page is refreshed (!) However, perhaps still faster then querying and maintaining the DB.
    try:
        _, airfieldsDict = AirfieldManager.loadAirfieldsFromFile()
        ar: AirfieldRecord = airfieldsDict[icaoCode]
        lat, lon = math.degrees(ar.lat), math.degrees(ar.lon)

        return flask.render_template('index.html', debugMode=DEBUG, date=date, dateTo=dateTo, icaoCode=icaoCode,
                                     linkPrevDay=linkPrevDay, linkNextDay=linkNextDay,
                                     dayRecords=dayRecords,
                                     lat=lat, lon=lon,
                                     showDatePicker=True)

    except KeyError as e:
        return flask.redirect('/')


@app.route('/reg/<registration>', methods=['GET'])
@app.route('/reg/<registration>/<date>', methods=['GET'])
@app.route('/reg/<registration>/<date>/<dateTo>', methods=['GET'])
def filterByRegistration(registration, date=None, dateTo=None):
    registration = saninitise(registration)

    if not registration:
        return flask.redirect('/')

    date = parseDate(date, default=datetime.now())
    dateTo = parseDate(dateTo) if dateTo else None

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

    display_tz = _getBrowserTimezone()
    dayRecords = []
    for i in range(numDays):
        currentDate = date + timedelta(days=i)

        numFlights, totalFlightTime = getSums(registration=registration, forDay=currentDate)
        totalFlightTime = formatDuration(totalFlightTime)
        departures, arrivals, flights = _prepareData(registration=registration, forDay=currentDate, display_tz=display_tz)

        dayRecord: DayRecord = DayRecord(date=currentDate, numFlights=numFlights, totalFlightTime=totalFlightTime,
                                         departures=departures, arrivals=arrivals, flights=flights)
        if numFlights > 0:
            dayRecords.append(dayRecord)

    return flask.render_template('index.html', debugMode=DEBUG, date=date, dateTo=dateTo, registration=registration,
                                 linkPrevDay=linkPrevDay, linkNextDay=linkNextDay,
                                 dayRecords=dayRecords,
                                 showFlightsOnly=True,
                                 showDatePicker=True)


def _prepareData(icaoCode=None, registration=None, forDay=None, limit=None, icaoFilter=[], sortTsDesc=False, orderByCol='takeoff_ts', display_tz=pytz.utc):

    if icaoCode:
        icaoCode = saninitise(icaoCode)

    if registration:
        registration = saninitise(registration)

    departures = listDepartures(icaoCode=icaoCode, registration=registration, forDay=forDay, limit=limit, icaoFilter=icaoFilter, sortTsDesc=sortTsDesc, display_tz=display_tz)
    arrivals = listArrivals(icaoCode=icaoCode, registration=registration, forDay=forDay, limit=limit, icaoFilter=icaoFilter, sortTsDesc=sortTsDesc, display_tz=display_tz)
    flights = listFlights(icaoCode=icaoCode, registration=registration, forDay=forDay, limit=limit, icaoFilter=icaoFilter,
                          sortTsDesc=sortTsDesc, orderByCol=orderByCol, display_tz=display_tz)

    return departures, arrivals, flights


@app.route('/search/<text>', methods=['GET'])
def search(text=None):
    text = saninitise(text)

    # TODO determine if that is an ICAO code or registration!

    if len(text) in (4, 6) and text.upper()[0:2] in afCountryCodes:
        return flask.redirect(f"/loc/{text.upper()}")
    else:
        return flask.redirect(f"/reg/{text}")


@app.route('/csv/<type>/<code>', methods=['GET'])
@app.route('/csv/<type>/<code>/<date>', methods=['GET'])
@app.route('/csv/<type>/<code>/<date>/<dateTo>', methods=['GET'])
def getCsv(type: str, code: str, date=None, dateTo=None):
    """
    :param type: loc | reg
    :param code: icaoCode | registration
    :param date:
    :param dateTo: optional
    :return:
    """
    if not type or not code:
        return flask.redirect('/')

    type = saninitise(type).upper()
    code = saninitise(code).upper()
    date = parseDate(date, default=datetime.now())
    dateTo = parseDate(dateTo, default=None, endOfTheDay=True)

    if dateTo:
        dateNow = datetime.now()
        if dateTo > dateNow:
            dateTo = dateNow

    numDays = limitDateRange(date, dateTo)

    display_tz = _getBrowserTimezone()
    flights = []
    for i in range(numDays):
        currentDate = date + timedelta(days=i)

        if type == 'LOC':
            flights += listFlights(icaoCode=code, forDay=currentDate, limit=200, display_tz=display_tz)
        elif type == 'REG':
            flights += listFlights(registration=code, forDay=currentDate, limit=200, display_tz=display_tz)
        else:
            return flask.redirect('/')

    csvText = _toFlightOfficeCsv(flights)

    output = flask.make_response(csvText)

    output.headers["Content-Disposition"] = f"attachment; filename={code}_{date.strftime('%Y-%m-%d')}.csv"
    output.headers["Content-type"] = "text/csv"

    return output


def _getFlightData(flight: LogbookItem):
    """
    @return [flightRecord] or errorResponse
    """
    if not flight:
        return flask.render_template('error40x.html', code=404, message=""), 404

    # TODO check user's access rights & rules
    # check flight >= -24H (data retention rule max 24H)
    if not eligibleForMapView(flight.takeoff_ts) and not flight.in_ps:
        return flask.render_template('error40x.html', code=410, message="The requested data is no longer available."), 410  # 410 = Gone ;)

    influxDbName = INFLUX_DB_NAME
    permanentStorage = PermanentStorageFactory.storageFor(flight.address_type)
    if permanentStorage.eligible4ps(flight.address):
        influxDbName = INFLUX_DB_NAME_PERMANENT_STORAGE

    influxDb = InfluxDbThread(dbName=influxDbName, host=INFLUX_DB_HOST, startThread=False)
    flightRecord = []

    addr = f"{addressPrefixes[flight.address_type]}{flight.address}"
    if flight.landing_ts:   # we are querying data for a complete flight
        q = f"SELECT lat, lon, alt, gs FROM pos WHERE addr='{addr}' AND time >= {flight.takeoff_ts}000000000 AND time <= {flight.landing_ts}000000000 order by time"
    else:   # this is a query on incomplete flight (takeoff_ts only)
        q = f"SELECT lat, lon, alt, gs FROM pos WHERE addr='{addr}' AND time >= {flight.takeoff_ts}000000000 order by time"

    rs = influxDb.client.query(query=q)
    if rs:
        for row in rs.get_points():
            row['dt'] = datetime.strptime(row['time'], '%Y-%m-%dT%H:%M:%SZ')
            flightRecord.append(row)
    else:
        return flask.render_template('error40x.html', code=404, message="No data."), 404

    return flightRecord


def _prepareDataForMap(flightRecord) -> (list, list):
    # detect continuous flight and out-of-signal segments:
    flightSegments = []
    skipSegments = []
    startIndex = 0
    for i in range(2, len(flightRecord)):
        if (flightRecord[i]['dt'] - flightRecord[i - 1]['dt']).seconds > 60:
            # print("DIFF:", (flightRecord[i]['dt'] - flightRecord[i - 1]['dt']).seconds)
            flightSegments.append(flightRecord[startIndex:i - 1])
            skipSegments.append(flightRecord[i - 2: i + 1])
            startIndex = i
    if startIndex > 0:
        flightSegments.append(flightRecord[startIndex:])  # ..till the end

    if len(flightSegments) == 0 and len(skipSegments) == 0:  # there was no signal outage
        flightSegments.append(flightRecord)

    return flightSegments, skipSegments


@app.route('/map/<flightId>', methods=['GET'])
def getMap(flightId: int):
    try:
        flightId = int(saninitise(flightId))
        print(f"[INFO] MAP: flightId='{flightId}'")
    except:
        print(f"[INFO] MAP: invalid flightId='{flightId}'")
        return flask.render_template('error40x.html', code=404, message="Nope :P"), 404

    display_tz = _getBrowserTimezone()

    flight: LogbookItem = getFlight(flightId=flightId, display_tz=display_tz)
    flightRecord = _getFlightData(flight=flight)
    if type(flightRecord) is not list:  # it is an error response in fact
        return flightRecord

    flightSegments, skipSegments = _prepareDataForMap(flightRecord)

    date = datetime.utcfromtimestamp(flight.takeoff_ts)
    # formatted dates for the search-sidebar date picker (YYYY-MM-DD):
    dateMin = (date - timedelta(days=14)).strftime("%Y-%m-%d")

    return flask.render_template('map.html',
                                 date=date,
                                 dateMin=dateMin,
                                 flight=flight,
                                 flightSegments=flightSegments,
                                 skipSegments=skipSegments)


@app.route('/api/fd/<flightId>', methods=['GET'])
def getFlightData(flightId: int):
    try:
        flightId = int(saninitise(flightId))
        print(f"[INFO] FD: flightId='{flightId}'")
    except:
        print(f"[INFO] FD: invalid flightId='{flightId}'")
        return flask.render_template('error40x.html', code=404, message="Nope :P"), 404

    flight: LogbookItem = getFlight(flightId=flightId, display_tz=_getBrowserTimezone())
    flightRecord = _getFlightData(flight=flight)
    if type(flightRecord) is not list:  # it is an error response in fact
        return flightRecord

    # transform into JSON structure to be used by leaflet:
    frSimplified = [{'dt': fr['dt'], 'lat': fr['lat'], 'lon': fr['lon']} for fr in flightRecord]  # add 'alt' later
    frSimplified.sort(key=lambda d: d['dt'])

    flightSegments, skipSegments = _prepareDataForMap(flightRecord)

    resp = {'flightSegments': flightSegments, 'skipSegments': skipSegments}

    return jsonify(resp)


@app.route('/api/ff', methods=['GET'])
def findFlights():
    date: datetime = parseDate(request.args.get("date", None), default=datetime.now(), endOfTheDay=True)
    loc: str = saninitise(request.args.get("loc", None))
    reg: str = saninitise(request.args.get("reg", None))
    cn: str = saninitise(request.args.get("cn", None))

    # TODO loc muze byt letiste startu nebo pristani

    if reg or cn:
        # TODO for reg & cn find device type + id
        pass

    # curl "http://localhost:5000/ff?date=2023-08-23&icao=LFNS&reg=OK1234&cn=IBI"

    if not loc and (not reg or not cn):
        return flask.render_template('error40x.html', code=404, message="Neumíme. Běž pryč! :P"), 404

    flights = listFlights(icaoCode=loc, forDay=date, limit=16)   # TODO toto chce nejake fikanejsi a elegantnejsi hledani

    resp = [{'id': f.id, 'reg': f.registration, 'cn': f.cn, 'to_ts': f.takeoff_ts, 'to_loc': f.takeoff_icao, 'la_ts': f.landing_ts, 'la_loc': f.landing_icao} for f in flights]
    resp.sort(key=lambda f: f['to_ts'])

    return jsonify(resp)


@app.route('/igc/<idType>/<flightId>', methods=['GET'])
def getIgc(idType: str, flightId: int):
    """
    :param idType   'f' flight or 't' takeoff id
    :param flightId flight or event ID
    """

    if idType not in ['f', 't']:
        return flask.render_template('error40x.html', code=404, message="Nope :P"), 404

    try:
        flightId = int(saninitise(flightId))
        # print(f"[INFO] IGC: flightId='{flightId}'")
    except ValueError:
        print(f"[INFO] IGC: invalid flightId='{flightId}'")
        return flask.render_template('error40x.html', code=404, message="Nope :P"), 404

    flight: LogbookItem = None
    if idType == 't':
        tmpFlightId = getFlightIdForTakeoffId(takeoffId=flightId)
        if tmpFlightId:
            flightId = tmpFlightId
            idType = 'f'    # let the following 'f'-if' do the heavy lifting
        else:
            flight: LogbookItem = getFlightInfoForTakeoff(takeoffId=flightId)
            flightRecord = _getFlightData(flight=flight)
            if type(flightRecord) is not list:  # it is an error response in fact
                return flightRecord

    if idType == 'f':
        flight = getFlight(flightId=flightId)
        flightRecord = _getFlightData(flight=flight)
        if type(flightRecord) is not list:  # it is an error response in fact
            return flightRecord

    igcText = flightToIGC(flightRecord, aircraftType=flight.aircraft_type, registration=flight.registration, competitionId=flight.cn)
    output = flask.make_response(igcText)

    date = flightRecord[0]['dt']
    output.headers["Content-Disposition"] = f"attachment; filename=flight_{flightId}_{date.strftime('%Y-%m-%d')}.igc"
    output.headers["Content-type"] = "text/plain"

    return output


@app.route('/stats', methods=['GET'])
def showStats():
    return flask.render_template('stats.html', date=datetime.now())


@app.route('/robots.txt', methods=['GET'])
def robots():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = saninitise(request.form.get('email', None))
        token = saninitise(request.form.get('token', None))
        print(f"[LOGIN] email: {email}; token: {token}")

    return flask.render_template('login.html')


# # http://localhost:8000/api/af/1/2/3/4
# @app.route('/api/af/<lat1>/<lat2>/<lon1>/<lon2>', methods=['GET'])
# def listAirfields(lat1: str, lat2: str, lon1: str, lon2: str):
#     try:
#         lat1 = float(_saninitise(lat1))
#         lat2 = float(_saninitise(lat2))
#         lon1 = float(_saninitise(lon1))
#         lon2 = float(_saninitise(lon2))
#
#     except ValueError:
#         return flask.render_template('error40x.html', code=404, message=":P"), 666
#
#     # TODO nejak rychle a svizne najit mezi vsemi letistmi..
#     airfields: list = airfieldManager.listInRange(lat1, lat2, lon1, lon2)
#
#     return json.dumps(airfields)


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

    rows = list()  # csv strings

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
        row.append(flight.max_alt)    # MAX_ALT
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

    print(f"DEBUG: {DEBUG}")
    if DEBUG:
        app.config['TEMPLATES_AUTO_RELOAD'] = True

    app.config['SECRET_KEY'] = 'some random key'

    app.run(debug=DEBUG)
