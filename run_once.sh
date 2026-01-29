#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# venv initialisation
cd "$SCRIPT_DIR"
sudo apt install chardet
python -m venv translate_venv
source translate_venv/bin/activate
pip install libretranslate
pip install libretranslatepy
deactivate
