#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source "$SCRIPT_DIR/translate_venv/bin/activate"
cd ..
libretranslate &
num_lib=$(ps|grep libretranslate)
cd -
sleep 2
python "$SCRIPT_DIR/translate_ch_en.py"
kill $num_lib 2>/dev/null
rm -rf ../db
