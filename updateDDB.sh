#!/bin/bash

#
# crontab entry:
# 0 4 * * * cd /home/ibisek/wqz/prog/python/ognLogbook; ./updateDDB.sh > /dev/null
#

cd /home/ibisek/wqz/prog/python/ognLogbook/

source ./venv/bin/activate
python3 ./src/ddbDataUpdater.py
deactivate

