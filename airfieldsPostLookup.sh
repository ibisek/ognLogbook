#!/bin/bash

source ./venv/bin/activate
export PYTHONPATH=.:./src:$PYTHONPATH

python src/experimental/airfieldsPostLookup.py

deactivate
