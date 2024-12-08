
import logging
import os
import sys

# detect we are in debug/dev mode:
DEBUG = False
val = sys.gettrace()
if val:
    DEBUG = True

# APRS_FILTER = 'r/+49.3678/+16.1145/1100'    # 1100 km ~ eastern Romania
APRS_FILTER = None

USE_MULTIPROCESSING_INSTEAD_OF_THREADS = False

if DEBUG:
    AIRFIELDS_FILE = '/home/ibisek/wqz/prog/python/ognLogbook/data/airfields.json'
    GEOFILE_PATH = '/home/ibisek/data/download/ognLogbook/500m/mosaic-500m.TIF'
else:
    AIRFIELDS_FILE = '/home/ibisek/wqz/prog/python/ognLogbook/data/airfields.json'
    GEOFILE_PATH = '/var/www/ognLogbook-data/mosaic-500m.TIF'
    USE_MULTIPROCESSING_INSTEAD_OF_THREADS = True

OGN_USERNAME = 'blume1'

redisConfig = {"host": "127.0.0.1", "password": "", "port": 6379}
REDIS_RECORD_EXPIRATION = 8*60*60     # [s]

AGL_LANDING_LIMIT = 100

# DB_HOST = '10.8.0.18'   # 127.0.0.1
DB_HOST = 'cml7'
# DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_NAME = 'ogn_logbook'
DB_USER = '**'
DB_PASSWORD = '**'
dbConnectionInfo = (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)

MAIL_HOST = 'smtp.centrum.cz'
MAIL_PORT = 587
MAIL_USER = '**'
MAIL_PASSWORD = '**'
MAIL_FROM = '**'
if MAIL_PASSWORD != '**':
    os.environ['MAIL_HOST'] = MAIL_HOST
    os.environ['MAIL_PORT'] = str(MAIL_PORT)
    os.environ['MAIL_USER'] = MAIL_USER
    os.environ['MAIL_PASSWORD'] = MAIL_PASSWORD
    os.environ['MAIL_FROM'] = MAIL_FROM

INFLUX_DB_NAME = DB_NAME
INFLUX_DB_HOST = DB_HOST
INFLUX_DB_NAME_PERMANENT_STORAGE = f"{INFLUX_DB_NAME}_ps"

if DB_PASSWORD != '**':
    os.environ['DB_HOST'] = DB_HOST
    os.environ['DB_PORT'] = str(DB_PORT)
    os.environ['DB_NAME'] = DB_NAME
    os.environ['DB_USER'] = DB_USER
    os.environ['DB_PASSWORD'] = DB_PASSWORD


MQ_HOST = 'mq.ibisek.com'
MQ_PORT = 1883
MQ_USER = '**'
MQ_PASSWORD = '**'

if MQ_PASSWORD != '**':
    os.environ['MQ_HOST'] = MQ_HOST
    os.environ['MQ_PORT'] = str(MQ_PORT)
    os.environ['MQ_USER'] = MQ_USER
    os.environ['MQ_PASSWORD'] = MQ_PASSWORD

# this enforces the SQLITE to be used:
# if 'SQLITE_DB_FILENAME' not in os.environ:
#     SQLITE_DB_FILENAME = '/home/ibisek/wqz/prog/python/ognLogbook/data/ognLogbook.sqlite'
#     os.environ.setdefault('SQLITE_DB_FILENAME', SQLITE_DB_FILENAME)

ADDRESS_TYPES = {0: 'S', 1: 'I', 2: 'F', 3: 'O'}
REVERSE_ADDRESS_TYPE = {'S': 0, 'I': 1, 'F': 2, 'O': 3}
ADDRESS_TYPE_PREFIX = {0: 'SKY', 1: 'ICA', 2: 'FLR', 3: 'OGN'}
REVERSE_ADDRESS_TYPE_PREFIX = {'SKY': 0, 'ICA': 1, 'FLR': 2, 'OGN': 3}
ADDRESS_TYPE_PREFIX_LETTER = {'S': 'SKY', 'I': 'ICA', 'F': 'FLR', 'O': 'OGN'}

DATA_AVAILABILITY_DAYS = 10
MAX_DAYS_IN_RANGE = 14

LOG_ROOT = '/tmp'
if os.name == 'nt':
    LOG_ROOT = 'e:/wqz/temp'

logging.basicConfig(filename=f"{LOG_ROOT}/rawWorker.log",
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
