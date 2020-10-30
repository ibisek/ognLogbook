
import pytz
from datetime import datetime, timezone, timedelta
from timezonefinder import TimezoneFinder


tf = TimezoneFinder()
lat, lon = -33.3804, -70.58017    # America/Santiago
tzName = tf.timezone_at(lng=lon, lat=lat)

print('tzName:', tzName)

remoteTz = pytz.timezone(tzName)
localTz = datetime.now().astimezone().tzinfo

nowHere = datetime.now(tz=localTz)
nowThere = datetime.now(tz=remoteTz)
print('now here: ', nowHere)
print('now there:', nowThere)

print('KOHEU.')
