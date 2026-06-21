# Python Tools

A collection of Python tools that can make a C developer's life a little easier, published here under MIT license. Where other people's work is used, it is clearly marked as such.

## autotranslate

Automatic translation from Chinese to English, meant for comments in code files. Chinese is detected based on the symbols used, so you can easily adapt it for any other language that doesn't use the latin alphabet. The tool uses [the external translation program `libretranslate`](https://www.libretranslate.com/). Translated text is added to the code as comments on the same line. Works for `C` and for a lot of other programming languages, and can easily be extended to include more programming languages.

**Note:** At the moment of writing these lines, there is a bug that only appears occasionally, where the local server running `libretranslate` refuses connections from the client API. Until this is dealt with, a workaround is to launch `libretranslate` manually once, and wait for the local server to start running before closing it; after this, `autotranslate` will run properly.

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

## c_tokeniser (partly lifted from [Coderay](https://github.com/rubychan/coderay))

Given a C source file as input, this tool tokenises C syntax and outputs results to json. This project is derivative; it was mostly transcribed from Coderay's code in [this Ruby source file](https://github.com/rubychan/coderay/blob/b5b3430d4635682b767c44469e28a70fe234187e/lib/coderay/scanners/c.rb). Coderay was made by Kornelius Kalnbach and published under [MIT license](https://github.com/rubychan/coderay/blob/228e87307c2faab06f854a79ab592a2737c20f65/MIT-LICENSE), which permits its use here.

## stringify

Barebones script that takes a text file and makes an altered copy with all the special characters escaped. A simplistic but useful tool for whenever you want to programmatically create a file.
