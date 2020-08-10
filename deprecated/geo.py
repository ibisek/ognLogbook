# """
# gdalinfo eu_dem_v11_E40N20-500m.TIF
# gdallocationinfo -wgs84  eu_dem_v11_E40N20-500m.TIF 16.1144561 49.3678764
# """
#
# import subprocess
#
# from configuration import GEOFILE_PATH
#
#
# class Geo(object):
#
#     GEOSCRIPT = '/home/ibisek/wqz/prog/python/ognLogbook/scripts/findElevation.sh'
#     GEOTIFF_ROOT_DIR = '/home/ibisek/wqz/prog/python/ognLogbook/data'
#
#     def getElevation(self, lat: float, lon: float):
#         cmd = f"{self.GEOSCRIPT} {self.GEOTIFF_ROOT_DIR} {lat} {lon}"
#         res = subprocess.run(cmd, shell=True, check=True, capture_output=True)
#
#         if res.stdout:
#             elev = float(res.stdout.decode('utf-8').strip())
#             return elev
#
#         return None
#
#
# if __name__ == '__main__':
#     lat = 49.3678764
#     lon = 16.1144561
#
#     geo = Geo()
#     elev = geo.getElevation(lat, lon)
#     print('ELEV:', elev)
#
#     # --
#
#     from math import radians
#
#     from osgeo import gdal
#     dataset = gdal.Open(GEOFILE_PATH, gdal.GA_ReadOnly)
#     geotransform = dataset.GetGeoTransform()
#
#     x = (lon - geotransform[0]) / geotransform[1]
#     y = (lat - geotransform[3]) / geotransform[5]
#
#     # import geoio
#     # img = geoio.GeoImage(fn)
#     # x, y = img.proj_to_raster(lon, lat)
#
#     # val = dataset.GetRasterBand(1).ReadAsArray(x, y, 1, 1)
#
#     width = dataset.RasterXSize
#     height = dataset.RasterYSize
#
#     # minx = geotransform[0]
#     # miny = geotransform[3] + width * geotransform[4] + height * geotransform[5]
#     # maxx = geotransform[0] + width * geotransform[1] + height * geotransform[2]
#     # maxy = geotransform[3]
#
#     # --
#     from osgeo import gdal, osr
#
#     # # get the existing coordinate system
#     # ds = gdal.Open(fn)
#     # old_cs = osr.SpatialReference()
#     # old_cs.ImportFromWkt(ds.GetProjectionRef())
#     #
#     # # create the new coordinate system
#     # wgs84_wkt = """
#     # GEOGCS["WGS 84",
#     #     DATUM["WGS_1984",
#     #         SPHEROID["WGS 84",6378137,298.257223563,
#     #             AUTHORITY["EPSG","7030"]],
#     #         AUTHORITY["EPSG","6326"]],
#     #     PRIMEM["Greenwich",0,
#     #         AUTHORITY["EPSG","8901"]],
#     #     UNIT["degree",0.01745329251994328,
#     #         AUTHORITY["EPSG","9122"]],
#     #     AUTHORITY["EPSG","4326"]]"""
#     # new_cs = osr.SpatialReference()
#     # new_cs.ImportFromWkt(wgs84_wkt)
#     #
#     # # create a transform object to convert between coordinate systems
#     # transform = osr.CoordinateTransformation(old_cs, new_cs)
#     #
#     # # get the coordinates in lat long
#     # latlong1 = transform.TransformPoint(minx, miny)
#     # latlong2 = transform.TransformPoint(maxx, maxy)
#     # latRange = (latlong1[0], latlong2[0])
#     # lonRange = (latlong1[1], latlong2[1])
#     #
#     # # longitude to x:
#     # pct = (lon - lonRange[0]) / (lonRange[1] - lonRange[0])
#     # # x = round(minx + (maxx-minx)*pct)
#     # xx = round(width * pct)
#     #
#     # # latitude to y:
#     # pct = (lat - latRange[0]) / (latRange[1] - latRange[0])
#     # # y = int(miny + (maxy - miny) * pct)
#     # yy = int(height * pct)
#     #
#     # val = dataset.GetRasterBand(1).ReadAsArray(xx, yy, 1, 1)
#     # print("val:", val)
#
#     # --
#     # srs = osr.SpatialReference()
#     # srs.ImportFromWkt(ds.GetProjection())
#     #
#     # srsLatLong = srs.CloneGeogCS()
#     # # Convert from (longitude,latitude) to projected coordinates
#     # ct = osr.CoordinateTransformation(srsLatLong, srs)
#     # (X, Y, height) = ct.TransformPoint(lon, lat)
#     #
#     # geomatrix = ds.GetGeoTransform()
#     # inv_geometrix = gdal.InvGeoTransform(geomatrix)
#     # x = int(inv_geometrix[0] + inv_geometrix[1] * X + inv_geometrix[2] * Y)
#     # y = int(inv_geometrix[3] + inv_geometrix[4] * X + inv_geometrix[5] * Y)
#
#     # --
#     # src = osr.SpatialReference()
#     # src.SetWellKnownGeogCS("WGS84")
#     #
#     # projection = dataset.GetProjection()
#     # dst = osr.SpatialReference(projection)
#     #
#     # ct = osr.CoordinateTransformation(src, dst)
#     # xy = ct.TransformPoint(lon, lat)
#     #
#     # x = (xy[0] - geotransform[0]) / geotransform[1]
#     # y = (xy[1] - geotransform[3]) / geotransform[5]
#
#     # --
#     tr = dataset.GetGeoTransform()
#     itr = gdal.InvGeoTransform(tr)
#
#     x = int(itr[0] + itr[1] * lon + itr[2] * lat)
#     y = int(itr[3] + itr[4] * lon + itr[5] * lat)
#
#     print("XXX")
#
#
