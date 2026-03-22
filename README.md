# Python Tools

A collection of Python tools that can make a C developer's life a little easier, published here under MIT license.

## autotranslate

Automatic translation from Chinese to English, meant for comments in code files. Chinese is detected based on the symbols used, so you can easily adapt it for any other language that doesn't use the latin alphabet. The tool uses the external translation program `libtranslate` (all rights reserved). Translated text is added to the code as comments on the same line. Works for `C` and for a lot of other programming languages, and can easily be extended to include more programming languages.

### Usage (Linux)

Run `run_once.sh` to create a virtual environment and install the prerequisites (please note that `chardet` will be installed globally). Then you can run the script with

```
# activate venv
source "$HOME/translate_venv/bin/activate"
# run translation script
python translate_ch_en.py <arguments>
# deactivate venv
deactivate
```

To see help documentation with more details, run it with the `-h` argument. **It is highly recommended that you read that documentation carefully before using the script in any other way.**

### Usage (Windows)

Run `run_once.ps1` to create a virtual environment and install the prerequisites (please note that `chardet` will be installed globally). Then you can run the script with

```
# activate venv
. $home\translate_venv\activate.ps1
# run translation script todo which python
python translate_ch_en.py <arguments>
# deactivate venv
deactivate
```

To see help documentation with more details, run it with the `-h` argument. **It is highly recommended that you read that documentation carefully before using the script in any other way.**

## cparser

Given a C source file as input, this tool parses C syntax (up to a point) and outputs results to json. The main logic was transcribed from `coderay`'s `ruby` code (todo repo link). A useful script if you want to make a tool such as an editor or a code-simplification aid. Or a [Bitfieldiser](https://github.com/VaiaPatta1985/Bitfieldiser)!

## stringify

Barebones script that takes a text file and makes an altered copy with all the special characters escaped. A simplistic but useful tool for whenever you want to programmatically create a file.
