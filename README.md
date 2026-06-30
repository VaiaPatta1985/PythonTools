# Python Tools

A collection of Python tools that can make a C developer's life a little easier, published here under MIT license. Where other people's work is used, it is clearly marked as such.

## `autotranslate` (dependencies: `chardet`, `libretranslate`, `libretranslatepy`)

Script for automatic translation from Chinese to English, meant for comments in code files. Chinese is detected based on the symbols used, so you can easily adapt it for any other language that doesn't use the latin alphabet. The tool uses [the external translation program `libretranslate`](https://www.libretranslate.com/). Translated text is added to the code as comments on the same line. Works for `C` and for a lot of other programming languages, and can easily be extended to include more programming languages.

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

## `c_tokeniser` (partly lifted from [Coderay](https://github.com/rubychan/coderay))

This tool can be used as a script but all its functionality is within functions, classes and objects you can import. When used as a script, you can use the `-h` argument to see usage details.

Given a C source file as input, the tool tokenises C syntax and outputs results to json. This project is derivative; it was mostly transcribed from Coderay's code in [this Ruby source file](https://github.com/rubychan/coderay/blob/b5b3430d4635682b767c44469e28a70fe234187e/lib/coderay/scanners/c.rb). Coderay was made by Kornelius Kalnbach and published under [MIT license](https://github.com/rubychan/coderay/blob/228e87307c2faab06f854a79ab592a2737c20f65/MIT-LICENSE), which permits its use here.

### Classes

Four `Enum`s are defined:
- `State`, whose values track the state of the C program as it is scanned.
- Three `Enum`s that characterise a specific entity found in the C code:
  - `TokenType`, which can be an item or a block;
  - `Action`, which - when not `'NONE''` - refers to items that start or end something;
  - `Kind`, which specifies exactly what the item is (eg a number, a variable, a keyword, etc).

The last three `Enum`s, together with the corresponding source text, form a named tuple called `Token`: `[('token_type', TokenType), ('action', Action), ('text', str), ('kind', Kind)]` (where `'text'`' may be empty in case `'action'` is not `'NONE'`).

### Objects

`ESCAPE`, `ESCAPED_ESCAPE`, and `UNICODE_ESCAPE` are regex patterns that characterise respectively Escape, escaped Escape, and Unicode Escape; they are used only to simplify the `MAIN_PATTERNS_<state>_STATE` dictionaries, defined on the next few lines. `MAIN_PATTERNS_<state>_STATE` and `SECONDARY_PATTERNS` are dictionaries that give meaningful names to the regex patterns from the original code. The main patterns are those that are checked on the first level, and secondary patterns are then used for disambiguation. `STATES_AND_PATTERNS` is a dictionary that tells the scanner which category of main patterns to look for (`MAIN_PATTERNS_INITIAL_STATE`, `MAIN_PATTERNS_STRING_STATE`, or `MAIN_PATTERNS_INCLUDE_EXPECTED_STATE`) based on the state of the scanned string. `KEYWORDS`, `DIRECTIVES`, `PREDEFINED_TYPES`, and `PREDEFINED_CONSTANTS` are tuples of C-specific keywords (again lifted from Coderay). Finally, the `TUPLE_TO_KIND` dictionary is used to map these keywords to elements of the `Kind` `Enum`, and `KINDS_OF_RESERVED_WORDS = TUPLE_TO_KIND.keys()` was added for speed and conceptual clarity. 

### Functions

The first three functions are only there to allow manipulations of regex objects in the same ways as bare regex patterns. The functions you probably want to call are the last two.

#### `one_of` (dependency: `re`)

Helper function. Performs an OR operation with regex *objects* rather with the patterns themselves.

#### `pattern_compose` (dependency: `re`)

Helper function. Performs concatenation with regex *objects* rather with the patterns themselves.

#### `zero_or_one` (dependency: `re`)

Helper function. Performs on a regex object the equivalent of `?` on a pattern.

#### `scan_tokens` (dependencies: `re`, `enum.Enum`, `typing.NamedTuple`, internal definitions)

Must be imported along with all the preceding definitions. It takes the C code in string form and returns a list of `Token` objects describing successive syntax elements. It was transcribed from Coderay, whose creator (**wisely**, as it turned out) chose Ruby to implement tokenisation.

#### `parse` (dependencies: `re`, `enum.Enum`, `typing.NamedTuple`, `json`, internal definitions)

Must be imported along with all the preceding definitions. This function calls `scan_tokens`, feeds it data from a given input file, and outputs the token list in json form to a given output file (or to the screen, which is the default). It is the entry point for the script.

## `stringify`

Barebones script that takes a text file and makes an altered copy with all the special characters escaped. A simplistic but useful tool for whenever you want to programmatically create a file. As usual, calling it with the `-h` argument prints more information on usage.
