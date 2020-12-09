# ognLogbook

Observes traffic data from the OGN network and maps take-offs and landings of small airplanes around the world.

https://logbook.ibisek.com/

## #TODO#
* ~~advanced flight analysis based on influx-stored data~~
* ~~avoid using GDAL from cmdline by opening the geotiff files in python and thus processing them way faster~~
* ~~create getAgl(latitude: float, longitude: float) function to get AGL [m] based on py-gdal~~
* process orphaned records in REDIS before they expire - detect possible field landings and out-of-signal situaltions 
