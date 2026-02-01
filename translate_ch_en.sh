#!/bin/bash

# DON'T RUN THIS WITHOUT ARGUMENTS BEFORE YOU READ THE HELP DOCS.
# To see the help docs, run `translate_ch_en.sh -h`

# activate venv
source "$HOME/translate_venv/bin/activate"

# run libretranslate in the background
# temporary folder db will be in /temp
cd /tmp || exit
libretranslate &
cd - || exit

# wait 2 seconds for libretranslate to start up
sleep 2
# run translation script
python "$( dirname -- "${BASH_SOURCE[0]}" )/translate_ch_en.py" "$@"
# deactivate venv
deactivate
# close libretranslate
kill $(pgrep libretranslate)
# delete temporary files
rm -rf /temp/db
