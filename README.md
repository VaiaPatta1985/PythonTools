# Python Tools

A collection of Python tools that can make a C developer's life a little easier, published here under MIT license. Where other people's work is used, it is clearly marked as such.

## `autotranslate` (dependencies: `chardet`, `libretranslate`, `libretranslatepy`)

Script for automatic translation from Chinese to English, meant for comments in code files. Chinese is detected based on the symbols used, so you can easily adapt it for any other language that doesn't use the latin alphabet. The tool uses [the external translation program `libretranslate`](https://www.libretranslate.com/). Translated text is added to the code as comments on the same line. Works for `C` and for a lot of other programming languages, and can easily be extended to include more programming languages.

### Usage (Linux)

Run `run_once.sh` to create a virtual environment and install the prerequisites. Then you can run the script with

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

Firstly, make sure that typing `python` in the PowerShell Terminal calls a **valid** python executable, as `$home\AppData\Local\Microsoft\WindowsApps\python.exe` may instead open Microsoft Store. (You may want to use [Python Install Manager](https://apps.microsoft.com/detail/9nq7512cxl7t) to sort this out.) Next, run `run_once.ps1` to create a virtual environment and install the prerequisites. Then you can run the script with

```
# activate venv
. $home\translate_venv\Scripts\Activate.ps1
# run translation script
python translate_ch_en.py <arguments>
# deactivate venv
deactivate
```

To see help documentation with more details, run it with the `-h` argument. **It is highly recommended that you read that documentation carefully before using the script in any other way.**

## `stringify`

Barebones script that takes a text file and makes an altered copy with all the special characters escaped. A simplistic but useful tool for whenever you want to programmatically create a file. As usual, calling it with the `-h` argument prints more information on usage.

## `assembly_made_easy`

Write assembly using readable names for registers, and leave it to this python script to turn it into proper x86-64 Assembly for you. It's written for NASM, ABI System V. It handles general-purpose registers and `xmm` registers, and can easily be extended to include other registers (just add them to the `ALL_REGISTERS` list). As usual, calling it with the `-h` argument prints more information on usage.
