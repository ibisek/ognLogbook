#!/bin/bash

#
# Terrain files: https://land.copernicus.eu/imagery-in-situ/eu-dem/eu-dem-v1.1
# apt install gdal-bin
#

if [ $# -ne 3 ]; then
    echo "Finds terrain elevation [m] in geospatial TIFF files"
    echo "  Usage: $0 <dem-files-root-dir> <latitude> <longitude>"
    exit 1
fi

dir=$1
lat=$2
lon=$3

#echo "dir: $dir"
#echo "lat: $lat"
#cho "lon: $lon"

for fn in $dir/*.TIF; do
    res=`gdallocationinfo -wgs84 -valonly $fn $lon $lat`
    if [ -n "$res" ]; then
	echo $res
	break
    fi
done

