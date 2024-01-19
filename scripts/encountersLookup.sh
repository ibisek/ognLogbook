#!/bin/bash

cd ..
source ./venv/bin/activate
export PYTHONPATH=./src:$PYTHONPATH

python3 ./src/cron/encountersLookup.py |tee -a ../encounters.log

cd -
deactivate
