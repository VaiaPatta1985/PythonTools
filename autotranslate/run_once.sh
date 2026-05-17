#!/bin/bash

# This script needs to run once to install prerequisites
# libretranslate and libretranslatepy are installed in a virtual environment
# the virtual environment ("translate_venv") is created within the home folder

# venv initialisation
python3 -m venv "$HOME/translate_venv"
source "$HOME/translate_venv/bin/activate"
pip install libretranslate libretranslatepy
deactivate
