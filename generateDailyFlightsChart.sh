#!/bin/bash
#
# crontab entry:
# 1 0 * * * cd /home/ibisek/wqz/prog/python/ognLogbook; ./generateDailyFlightsChart.sh
#

source ./venv/bin/activate

export PYTHONPATH=.:./src:$PYTHONPATH

python3 ./src/experimental/dailyFlights.py

deactivate
