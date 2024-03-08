#!/usr/bin/env bash

python3 -m venv venv
source venv/bin/activate
clear

pip install -r REQUIREMENTS.txt
python3 main.py