#!/bin/bash

cd /home/ibisek/wqz/prog/python/ognLogbook/

source ./venv/bin/activate
python3 ./src/ddbDataUpdater.py
deactivate

