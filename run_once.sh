#!/bin/bash

# venv initialisation
python -m venv translate_venv
source translate_venv/bin/activate
pip install libretranslate
pip install libretranslatepy
deactivate
