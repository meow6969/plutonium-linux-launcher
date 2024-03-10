#!/usr/bin/env bash

python3 -m venv venv
source venv/bin/activate
pip install -r REQUIREMENTS.txt
clear

python3 main.py