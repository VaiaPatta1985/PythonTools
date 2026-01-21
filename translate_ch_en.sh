#!/bin/bash

source translate_venv/bin/activate
cd ..
libretranslate &
num_lib=$(ps|grep libretranslate)
cd -
sleep 2
file_types_to_translate="qml 001 js"
rm -rf batch_raw 2>/dev/null
rm -rf batch_raw_tr 2>/dev/null
rm -rf batch_ch 2>/dev/null
rm -rf uncertain.csv 2>/dev/null
for ep in $file_types_to_translate
do
    grep -IHnr -e [^0-9a-zA-Z[:punct:][:space:]] $(find . -name "*.${ep}")>>batch_raw
done
grep -ho -e '[^0-9a-zA-Z[:punct:][:space:]╖и└╝╘▓╗╖▒▀╜╟┐к┐╦╡├ў┌╡─╛╪╨╬┤°┬▌┐╩╫┤╬░▓╫░╫в╥т╩┬╧ю╫╡─╛╪╨╬┤°▒ъ╛╪╨╬╘▓╜╟╛╪╨╬┤°▓╗═м▒▀╜╟░ы╛╢╡─L╨═╓з╝▄└╫┤я═╝╘▓╗╖┤°▒ъ╞╒═и╚¤╜╟╨╬┤°╘▓┐╫╡─╛╪╨╬╖и└╝┤°┬▌┐╫╡─╘▓L╨═╓з╝▄╝№▓█╘▓╗╖┤°▒ъ╘▓╗╖╞╜╨╨╦─▒▀╨╬▓╗═м▒▀╜╟┐к┐┌╡─╛╪╨╬╘▓╜╟L╨═╓з╝▄┤°╛╪╨╬┐╫╡─╛╪╨╬╖и└╝].*$' batch_raw>batch_ch
#./clean_up_db.sh &
#num_clean=$(ps|grep clean_up_db)
num_sleep=$(ps|grep sleep)
python translate_ch_en.py
kill $num_lib 2>/dev/null
#kill $num_clean 2>/dev/null
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
