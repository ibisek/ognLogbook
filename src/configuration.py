
import os

APRS_FILTER = 'r/+49.3678/+16.1145/250'
# APRS_FILTER = None

SPEED_THRESHOLD = 50    # [km/h]

redisConfig = {"host": "127.0.0.1", "password": "", "port": 6379}
REDIS_RECORD_EXPIRATION = 12*60*60     # [s]


DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_NAME = 'ogn_logbook'
DB_USER = '**'
DB_PASSWORD = '**'
dbConnectionInfo = (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)

if DB_PASSWORD != '**':
    os.environ.setdefault('DB_HOST', DB_HOST)
    os.environ.setdefault('DB_PORT', str(DB_PORT))
    os.environ.setdefault('DB_NAME', DB_NAME)
    os.environ.setdefault('DB_USER', DB_USER)
    os.environ.setdefault('DB_PASSWORD', DB_PASSWORD)


# this enforces the SQLITE to be used:
# if 'SQLITE_DB_FILENAME' not in os.environ:
#     SQLITE_DB_FILENAME = '/home/ibisek/wqz/prog/python/ognLogbook/data/ognLogbook.sqlite'
#     os.environ.setdefault('SQLITE_DB_FILENAME', SQLITE_DB_FILENAME)

