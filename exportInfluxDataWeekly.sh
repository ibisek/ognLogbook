#!/bin/bash
#
# crontab entry:
# 0 5 * * 0 cd /home/ibisek/wqz/prog/python/ognLogbook; ./exportInfluxDataWeekly.sh > /dev/null
#

source ./venv/bin/activate

export PYTHONPATH=.:./src:$PYTHONPATH

python3 ./src/experimental/influx_exportData_weekly.py

deactivate
