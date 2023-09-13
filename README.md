# ognLogbook

Observes traffic data from the OGN network and maps take-offs and landings of small airplanes around the world.

https://logbook.ibisek.com/

## #TODO#
* airfield flags into map?
* encounters (!!) detection and visualisation
* user management
* fleet management for users
* mailing queue
* configurable event watcher
    - notifications on lost/stolen units
* flight track into email upon landing?
* recognition of short winch flights, especially exceptional situation handling (2min flight limit vs. winch 'jumps')

* ~~advanced flight analysis based on influx-stored data~~
* ~~avoid using GDAL from cmdline by opening the geotiff files in python and thus processing them way faster~~
* ~~create getAgl(latitude: float, longitude: float) function to get AGL [m] based on py-gdal~~
* ~~process orphaned records in REDIS before they expire - detect possible field landings and out-of-signal situaltions~~
* ~~all time info to local TZ (using https://github.com/evansiroky/timezone-boundary-builder)~~
* ~~add MAX_ALT to .csv file (during flight distance calculation)~~
* ~~flight track map inversion (fetch data via api)~~
