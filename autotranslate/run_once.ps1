# This script needs to run once to install prerequisites
# libretranslate and libretranslatepy are installed in a virtual environment
# the virtual environment ("translate_venv") is created within the home folder

# venv initialisation
$python_exec = (Get-Command python|Select-Object Source).Source
start -argumentlist "-m venv $home\translate_venv" -filepath "$python_exec" -wait -nonewwindow
. $home\translate_venv\scripts\activate.ps1
pip install libretranslate libretranslatepy
deactivate
