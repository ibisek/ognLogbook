"""
Reads a geofile TIFF containing terrain altitude information.
"""

import gdal
import struct

import osgeo.gdal
from osgeo.osr import SpatialReference, CoordinateTransformation


class Geofile(object):

    FILENAME = '/tmp/00/mosaic-500m.TIF'

    def __init__(self, filename=FILENAME):
        print(f"[INFO] Reading geofile from '{filename}'")
        self.dataset = gdal.Open(filename, gdal.GA_ReadOnly)
        self.geotransform = self.dataset.GetGeoTransform()
        self.band = self.dataset.GetRasterBand(1)

        srcRef = SpatialReference()
        srcRef.SetWellKnownGeogCS("WGS84")
        dstRef = SpatialReference(self.dataset.GetProjection())
        self.ct = CoordinateTransformation(srcRef, dstRef)

        gdalVersion = osgeo.gdal.__version__
        print(f"[INFO] Using gdal ver. {gdalVersion}")
        self.gdalMajorVer = int(gdalVersion[:gdalVersion.find('.')])

    def getValue(self, lat, lon):
        if self.gdalMajorVer < 3:
            xy = self.ct.TransformPoint(lon, lat)
        else:
            xy = self.ct.TransformPoint(lat, lon)   # since gdal ver.3 they flipped order of the arguments (!)

        x = (xy[0] - self.geotransform[0]) / self.geotransform[1]  # geotransform : (ulx, xres, xskew, uly, yskew, yres)
        y = (xy[1] - self.geotransform[3]) / self.geotransform[5]

        try:  # in case raster isn't full extent
            structval = self.band.ReadRaster(xoff=int(x), yoff=int(y), xsize=1, ysize=1, buf_type=self.band.DataType)
            intval = struct.unpack('f', structval)  # assume float
            val = intval[0]
        except:
            val = None

        return val


if __name__ == '__main__':
    lat = 49.3678625    # Krizanov (LKKA)
    lon = 16.1144897

    # lat = 57.6960022  # Borås flygplats (ESGE)
    # lon = 12.8449750

    gf = Geofile()
    val = gf.getValue(lat, lon)
    print('val:', val)
