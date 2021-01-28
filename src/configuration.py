
import os
import sys

# detect we are in debug/dev mode:
DEBUG = False
val = sys.gettrace()
if val:
    DEBUG = True

# APRS_FILTER = 'r/+49.3678/+16.1145/1100'    # 1100 km ~ eastern Romania
APRS_FILTER = None

if DEBUG:
    AIRFIELDS_FILE = '/home/ibisek/wqz/prog/python/ognLogbook/data/airfields.json'
    GEOFILE_PATH = '/home/ibisek/data/download/ognLogbook/500m/mosaic-500m.TIF'
else:
    AIRFIELDS_FILE = '/home/ibisek/wqz/prog/python/ognLogbook/data/airfields.json'
    GEOFILE_PATH = '/var/www/ognLogbook-data/mosaic-500m.TIF'

redisConfig = {"host": "127.0.0.1", "password": "", "port": 6379}
REDIS_RECORD_EXPIRATION = 8*60*60     # [s]

AGL_LANDING_LIMIT = 100

# DB_HOST = '10.8.0.18'   # 127.0.0.1
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_NAME = 'ogn_logbook'
DB_USER = '**'
DB_PASSWORD = '**'
dbConnectionInfo = (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)

INFLUX_DB_NAME = DB_NAME
INFLUX_DB_HOST = DB_HOST

if DB_PASSWORD != '**':
    os.environ.setdefault('DB_HOST', DB_HOST)
    os.environ.setdefault('DB_PORT', str(DB_PORT))
    os.environ.setdefault('DB_NAME', DB_NAME)
    os.environ.setdefault('DB_USER', DB_USER)
    os.environ.setdefault('DB_PASSWORD', DB_PASSWORD)


MQ_HOST = 'mq.ibisek.com'
MQ_PORT = 1883
MQ_USER = '**'
MQ_PASSWORD = '**'

if MQ_PASSWORD != '**':
    os.environ.setdefault('MQ_HOST', MQ_HOST)
    os.environ.setdefault('MQ_PORT', str(MQ_PORT))
    os.environ.setdefault('MQ_USER', MQ_USER)
    os.environ.setdefault('MQ_PASSWORD', MQ_PASSWORD)

# this enforces the SQLITE to be used:
# if 'SQLITE_DB_FILENAME' not in os.environ:
#     SQLITE_DB_FILENAME = '/home/ibisek/wqz/prog/python/ognLogbook/data/ognLogbook.sqlite'
#     os.environ.setdefault('SQLITE_DB_FILENAME', SQLITE_DB_FILENAME)

ADDRESS_TYPES = {1: 'I', 2: 'F', 3: 'O'}
ADDRESS_TYPE_PREFIX = {1: 'ICA', 2: 'FLR', 3: 'OGN'}
REVERSE_ADDRESS_TYPE_PREFIX = {'ICA': 1, 'FLR': 2, 'OGN': 3}

MAX_DAYS_IN_RANGE = 14
