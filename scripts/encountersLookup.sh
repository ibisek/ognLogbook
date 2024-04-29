#!/bin/bash

cd ..
source ./venv/bin/activate
export PYTHONPATH=./src:$PYTHONPATH

python3 -u ./src/cron/encounters/encountersLookup2.py |tee -a ../encounters.log

cd -
deactivate
