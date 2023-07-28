#!/bin/bash
#
# crontab entries:
# 0 1 * * tue cd /home/ibisek/wqz/prog/python/ognLogbook && INFLUX_DB_NAME='ogn_logbook_ps' && ./scripts/exportInfluxDataWeekly.sh > /dev/null
# 0 3 * * tue cd /home/ibisek/wqz/prog/python/ognLogbook && INFLUX_DB_NAME='ogn_logbook' && ./scripts/exportInfluxDataWeekly.sh > /dev/null
#

source ./venv/bin/activate

export PYTHONPATH=.:./src:$PYTHONPATH

#export INFLUX_DB_NAME='ogn_logbook'
#export INFLUX_DB_NAME='ogn_logbook_stm'
echo "Using INFLUX_DB_NAME: '$INFLUX_DB_NAME'"

export STORAGE_DIR='/media/data/archive'

python3 ./src/experimental/influx_exportData_weekly.py

deactivate
