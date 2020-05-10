
APRS_FILTER = 'r/+49.3678/+16.1145/250'
# APRS_FILTER = None

SPEED_THRESHOLD = 40    # [km/h]

redisConfig = {"host": "127.0.0.1", "password": "", "port": 6379}
REDIS_RECORD_EXPIRATION = 12*60*60     # [s]

NUM_RAW_WORKERS = 2

DB_URL = '127.0.0.1'
DB_PORT = 3306
DB_NAME = 'ogn_logbook'
DB_USER = '**'
DB_PASSWORD = '**'
dbConnectionInfo = (DB_URL, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)

