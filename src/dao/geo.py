
import subprocess


GEOSCRIPT = '/home/ibisek/wqz/prog/python/ognLogbook/scripts/findElevation.sh'
GEOTIFF_ROOT_DIR = '/home/ibisek/wqz/prog/python/ognLogbook/data'


def getElevation(lat: float, lon: float):
    cmd = f"{GEOSCRIPT} {GEOTIFF_ROOT_DIR} {lat} {lon}"
    res = subprocess.run(cmd, shell=True, check=True, capture_output=True)

    if res.stdout:
        elev = float(res.stdout.decode('utf-8').strip())
        return elev

    return None


if __name__ == '__main__':
    lat = 49.3678764
    lon = 16.1144561
    elev = getElevation(lat, lon)

    print('ELEV:', elev)
