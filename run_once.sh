#!/bin/bash

# This script needs to run once to install prerequisites
# chardet is installed globally
# libretranslate and libretranslatepy are installed in a virtual environment
# the virtual environment ("translate_venv") is created within the home folder

# install chardet for encoding detection
source /usr/lib/os-release
if [ "$ID_LIKE" == debian ]
then
  sudo apt install chardet
else
  sudo yum install chardet
fi
# venv initialisation
python -m venv "$HOME/translate_venv"
source "$HOME/translate_venv/bin/activate"
pip install libretranslate
pip install libretranslatepy
deactivate
