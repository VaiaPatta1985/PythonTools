#!/bin/bash

# DON'T RUN THIS WITHOUT ARGUMENTS BEFORE YOU READ THE HELP DOCS.
# To see the help docs, run `translate_ch_en.sh -h`

# activate venv
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source "$SCRIPT_DIR/translate_venv/bin/activate"

# run libretranslate in the background
# temporary folder db will be outside working directory
cd ..
libretranslate &
cd -

# wait 2 seconds for libretranslate to start up
sleep 2
# run translation script
python "$SCRIPT_DIR/translate_ch_en.py" "$@"
# close libretranslate
kill $(pgrep libretranslate)
# delete temporary files
rm -rf ../db
