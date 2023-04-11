#!/bin/bash
#
# crontab entry:
# 0 5 * * mon cd /home/ibisek/wqz/prog/python/ognLogbook/scripts; ./exportInfluxDataWeekly.sh > /dev/null
#

source ./venv/bin/activate

export PYTHONPATH=.:./src:$PYTHONPATH

export INFLUX_DB_NAME='ogn_logbook'
#export INFLUX_DB_NAME='ogn_logbook_stm'
export STORAGE_DIR='/media/data/archive'

python3 ./src/experimental/influx_exportData_weekly.py

deactivate
