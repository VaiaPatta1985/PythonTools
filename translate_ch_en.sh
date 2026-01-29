#!/bin/bash

source translate_venv/bin/activate
cd ..
libretranslate &
num_lib=$(ps|grep libretranslate)
cd -
sleep 2
python translate_ch_en.py
kill $num_lib 2>/dev/null
rm -rf ../db
