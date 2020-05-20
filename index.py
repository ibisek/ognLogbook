"""
Created on 20. 5. 2020

@author: ibisek
"""

import sys
import flask
import getopt

from configuration import dbConnectionInfo
from db.DbSource import DbSource
from dao.logbookDao import listDepartures, listArrivals,listFlights


app = flask.Flask(__name__)


@app.route('/')
def index():
    dbSource = DbSource(dbConnectionInfo=dbConnectionInfo)
    # TODO ..

    departures = listDepartures()
    arrivals = listArrivals()
    flights = listFlights()

    return flask.render_template('index.html', departures=departures, arrivals=arrivals, flights=flights)


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


if __name__ == '__main__':

    debugMode = False

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
