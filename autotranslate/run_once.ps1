winget install uchardet
# todo which python
start -argumentlist "-m venv $home\translate_venv" -filepath "$home\appdata\local\programs\python\Python314\python.exe" -wait -nonewwindow
. $home\translate_venv\activate.ps1
pip install libretranslate
pip install libretranslatepy
deactivate

