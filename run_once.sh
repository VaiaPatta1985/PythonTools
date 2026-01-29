#!/bin/bash

# This script needs to run once to install prerequisites
# chardet is installed globally
# libretranslate and libretranslatepy are installed in a virtual environment
# the virtual environment ("translate_venv") is created within the script folder

# install chardet for encoding detection
sudo apt install chardet

# venv initialisation
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"
python -m venv translate_venv
source translate_venv/bin/activate
pip install libretranslate
pip install libretranslatepy
deactivate
