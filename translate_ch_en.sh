#!/bin/bash

source translate_venv/bin/activate
cd ..
libretranslate &
num_lib=$(ps|grep libretranslate)
cd -
sleep 2
num_sleep=$(ps|grep sleep)
python translate_ch_en.py
kill $num_lib 2>/dev/null
kill $num_sleep 2>/dev/null
rm -rf ../db
for p in $file_types_to_translate
do
    find . -name "*.${p}_tr*" -print0 | while IFS= read -r -d '' file
    do
        lfile=$((${#file} - 3))
        mv "$file" "${file:0:${lfile}}"
    done
done
