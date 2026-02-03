"""
Python script to translate chinese found within code (be it in comments, in strings, or elsewhere) to english.
It runs on all files with given extensions within the specified folder. Output file can replace input file (default).
The english translation is appended to the end of the line as a comment. The script uses a local libtranslate server.
Run with the `-h` argument for more details.
"""

import re
import argparse
from os import path, walk, getenv, chdir, system
from time import sleep
from shutil import rmtree
from codecs import lookup
from chardet import detect
from libretranslatepy import LibreTranslateAPI


# general constants
LOCAL = 'http://127.0.0.1:5000/'
#TEMP_FOLDER = getenv('TMP')
TEMP_FOLDER = '/tmp'

# natural language constants
ENGLISH_LANGUAGE_CODE = "en"
CHINESE_LANGUAGE_CODE = "zh-Hans"
CHINESE_PATTERN_UNICODE = r'[\u3400-\u4DBF\u4E00-\u9FFF]'  # regular expression matches Unicode Chinese characters
CSV_SEPARATOR = '妈'  # a simple single-character Chinese word that will probably never appear in code (it means "mum")
CSV_HEADER = CSV_SEPARATOR.join(['filename', 'line number', 'chinese', 'translation\n'])

TOO_LONG = 60000  # 60000 is assuming you want to open the csv with LibreOffice Calc; for Microsoft Excel, use 30000
RESTART_EVERY = 500  # restart the API after so many uses, and clear cache; this is for speed

# programming language constants
COMMENT_START_END = {
    'qml': ['//', ''], 'js': ['//', ''], 'c': ['//', ''], 'cpp': ['//', ''], 'exp': ['//', ''],
    'py': ['#', ''], 'rb': ['#', ''], 'sh': ['#', ''], 'bash': ['#', ''], 'ps1': ['#', ''],
    'bat': ['::', ''],
    'bas': ['\'', ''],

    '001': ['(*', '*)'],
}
ALL_SUPPORTED_FILE_TYPES = COMMENT_START_END.keys()

# defaults

# default filenames
RAW_FILE = 'batch_raw'
CH_FILE = 'batch_ch'
TRANS_RAW_FILE = 'batch_raw_tr'
LIST_FILE = 'uncertain.csv'
# default encoding
DEFAULT_ENCODING = 'utf-8'
# default file extensions
DEFAULT_TYPES = ALL_SUPPORTED_FILE_TYPES


def detect_encodings(filenames: list[str]) -> dict[str, str]:
    """
    Uses chardet to detect text encoding for each file.
    :param filenames: a list of absolute file paths
    :return: a dictionary matching each of the given files to its encoding
    """
    dict_out: dict[str, str] = {}
    for fn in filenames:
        with open(fn, "rb") as rf:
            raw = rf.read()
        dict_out[fn] = detect(raw)["encoding"]
    return dict_out


def make_raw_line_list(file_encs: dict[str, str]) -> list[list[str]]:
    """
    Given files with known encodings, outputs list of info for each line that contains chinese characters.
    This info for each line is a list of the following data:
     - filepath
     - line number in string form
     - the entire line
     - the chinese characters from that line
    :param file_encs: dictionary matching each file to its text encoding
    :return: list of [filepath, str(line number), line, chinese] lists (for each line that contains chinese)
    """
    splitlines_all: list[list[str]] = []
    for fn, enc in file_encs.items():
        with open(fn, "r", encoding=enc) as raw:
            all_lines = raw.readlines()
        for line_idx in range(len(all_lines)):
            cur_line = all_lines[line_idx]
            chinese = re.findall(CHINESE_PATTERN_UNICODE, cur_line)
            if chinese:
                splitline = [fn, str(line_idx+1), cur_line, chinese]
                splitlines_all.append(splitline)
    return splitlines_all


def get_filenames(f_path: str, extensions: list[str]) -> list[str]:
    """
    Finds files with given extensions contained in a folder and its subfolders.
    :param f_path: the folder to recursively search
    :param extensions: the file extensions to look for
    :return: list of files with given extensions contained in the folder and its subfolders
    """
    files_found = []
    for root, dirs, files in walk(f_path):
        for file in files:
            if file.split('.')[-1].lower() in extensions:
                files_found.append(path.join(root, file))
    return files_found


def start_libtranslate_server():
    """

    :return:
    """
    previousdir = path.curdir
    chdir(TEMP_FOLDER)
    system('libtranslate')  # TODO don't wait for it to finish! run in background!
    chdir(previousdir)
    pass


def translate_code(fullpath: str, ext_in: list[str]=DEFAULT_TYPES, pref: str='', suff: str='',
                   raw_file: str=RAW_FILE, ch_file: str=CH_FILE, trans_raw_file: str=TRANS_RAW_FILE,
                   list_file: str=LIST_FILE, char_encoding: str=DEFAULT_ENCODING) -> None:
    """
    The main program. Translates chinese from all files with given extensions in a given folder and its subfolders,
    appends english translation as a comment at the end of each line, and saves the translated file to the same path as
    the original. The name of the translated file derives from the original file with a prefix and/or suffix appended.

    ATTENTION: If neither prefix nor suffix is specified (and set to nonempty) then the original file will be replaced.
               THIS IS THE DEFAULT BEHAVIOUR.

    Other outputs include:
    - files listing data per line containing chinese; by default, these files are saved to the working directory.
      - raw_file contains every line containing chinese, along with its location [filepath, line number]
        (in csv form; csv separator is CSV_SEPARATOR)
      - ch_file contains the isolated chinese from each line in raw_file
      - trans_raw_file contains every translated line (ie original line containing chinese plus commented translation),
        along with its location [filepath, line number] (in csv form; csv separator is CSV_SEPARATOR)
      - list_file contains the isolated chinese and the translation for each line, along with filepath and line number
        (in csv form; csv separator is CSV_SEPARATOR; header is CSV_HEADER)
    - progress info printed to screen
    - info on very large lines encountered, printed to screen; you may want to exclude these lines from your csv if you
      want to open it with LibreOffice or MS Office (also, for MS Office you should lower the limit, given by TOO_LONG).
    :param fullpath: folder containing all the files
    :param ext_in: list of file types to translate (default is all supported file types)
    :param pref: prefix to add to output file; default is none; IF NO PREFIX AND NO SUFFIX, ORIGINAL FILE IS REPLACED
    :param suff: suffix to add to output file; default is none; IF NO PREFIX AND NO SUFFIX, ORIGINAL FILE IS REPLACED
    :param raw_file: file to record [filename, line number, line content] tuple for each line containing chinese,
                     separated by the character given by CSV_SEPARATOR (default is given by RAW_FILE)
    :param ch_file: file to record isolated chinese content for each line in raw_file (default is given by CH_FILE)
    :param trans_raw_file: this file (default given by TRANS_RAW_FILE) will contain each line of raw_file with
                           the translation of its chinese content appended as a comment
    :param list_file: csv file (whose separator is CSV_SEPARATOR) that contains [file path, line number (as a string),
                      chinese content, translation] for each line containing chinese (default is given by LIST_FILE);
                      header is given by CSV_HEADER
    :param char_encoding: expected test encoding (default given by DEFAULT_ENCODING); use 'detect' to run encoding
                      detection for each file.
    :return: None
    """
    print("Starting libtranslate server.")
    start_libtranslate_server()
    print("Started libtranslate server. Waiting for startup.")
    sleep(2)
    print("Gathering filenames.")
    files_of_desired_types = get_filenames(fullpath, ext_in)
    if char_encoding == 'detect':
        print("Detecting encodings.")
        encs = detect_encodings(files_of_desired_types)
        print("Encodings detected.")
    else:
        encs = {filename: char_encoding for filename in files_of_desired_types}
    splitlines = make_raw_line_list(encs)
    print("Found all lines pending translation.")

    all_files_repeated: list[str] = [splitline[0] for splitline in splitlines]
    line_nums: list[str] = [splitline[1] for splitline in splitlines]
    ch_lines: list[str] = [splitline[3] for splitline in splitlines]
    num_lines = len(splitlines)
    raw_lines = [CSV_SEPARATOR.join(splitline[0:3]) for splitline in splitlines]
    csv_lines = [CSV_HEADER]

    with open(raw_file, "w", encoding=DEFAULT_ENCODING) as out_raw_file:
        out_raw_file.writelines(raw_lines)
    print("Recorded all lines pending translation.")

    # write csv lines excluding english translation
    for line in splitlines:
        line_to_add = line[0:2]
        line_to_add.append(line[3].removesuffix('\n'))
        csv_lines.append(CSV_SEPARATOR.join(line_to_add))

    all_files = list(set(all_files_repeated))

    print('Files have been listed.')

    with open(ch_file, "w", encoding=DEFAULT_ENCODING) as out_file:
        out_file.writelines(ch_lines)

    print('Chinese phrases have been catalogued.')

    tr_lines = [str(k) for k in range(num_lines)]  # just preallocating
    fff = 0
    too_large: list[str] = []
    for line in ch_lines:
        if len(line) > TOO_LONG:
            too_large.append(raw_lines[fff])
        if not fff % RESTART_EVERY:  # restart the API after so many uses, and clear cache; this is for speed
            rmtree(path.join(TEMP_FOLDER, 'db'))
            lt = LibreTranslateAPI(LOCAL)
        # the entire point of this project: finally translate :)
        tr_lines[fff] = lt.translate(line.removesuffix('\n'), CHINESE_LANGUAGE_CODE, ENGLISH_LANGUAGE_CODE)
        fff = fff + 1
        print('Translated line '+str(fff)+' of '+str(num_lines)+'.')

    rmtree(path.join(TEMP_FOLDER, 'db'))
    print('Translation has taken place.')
    print('Info on lines that are too large:')
    for itm in too_large:
        print('-------------')
        print(itm)

    # append "end comment" symbol to translation
    for idx in range(num_lines):
        ext = all_files_repeated[idx].split('.')[-1].lower()
        if COMMENT_START_END[ext][1] and not tr_lines[idx].endswith(COMMENT_START_END[ext][1]):
            tr_lines[idx] = tr_lines[idx]+COMMENT_START_END[ext][1]
        csv_lines[idx + 1] = CSV_SEPARATOR.join([csv_lines[idx + 1], tr_lines[idx]+'\n'])

    # can't remember why I did it this way tbh

    with open(list_file, "w", encoding=DEFAULT_ENCODING) as out_file:
        out_file.writelines(csv_lines)

    print('Changes have been listed.')

    out_lines = [raw_lines[idx].removesuffix('\n') + ' ' + \
                 COMMENT_START_END[all_files_repeated[idx].split('.')[-1].lower()][0] + tr_lines[idx] + \
                 '\n' for idx in range(num_lines)]
    with open(trans_raw_file, "w", encoding=DEFAULT_ENCODING) as f_out:
        f_out.writelines(out_lines)
    print("Full data has been recorded.")

    nf = len(all_files)
    f = 0
    # create the translated files
    for filename in all_files:
        f = f + 1
        ext = filename.split('.')[-1].lower()
        # read original
        with open(filename, "r", encoding=encs[filename]) as f_in:
            in_lines = f_in.readlines()
        rep_idx = 0
        while all_files_repeated[rep_idx] != filename:
            rep_idx = rep_idx + 1
        while all_files_repeated[rep_idx] == filename:
            # append translation as a comment, to each line containing chinese
            in_lines[int(line_nums[rep_idx]) - 1] = \
                    in_lines[int(line_nums[rep_idx]) - 1].removesuffix('\n') + \
                    ' '+COMMENT_START_END[ext][0]+tr_lines[rep_idx]+'\n'
            rep_idx = rep_idx + 1
            if rep_idx == num_lines:
                break
        # write to file with specified filename
        split_filename = path.split(filename)
        out_filename = split_filename[0] + pref + \
                       split_filename[1].removesuffix('.'+ext).removesuffix('.'+ext.upper()) + suff + '.' + ext
        with open(out_filename, "w", encoding=encs[filename]) as f_out:
            f_out.writelines(in_lines)
        print("Translated file " + str(f) + " of " + str(nf) + ".")


def standalone_cli():
    """
    The CLI interface. All command line parameters are optional.
    Call the script with the `-h` argument for a detailed explanation.
    """
    my_args = argparse.ArgumentParser(add_help=True, formatter_class=argparse.RawDescriptionHelpFormatter, description=
"""
This python script uses libtranslate and its python API to translate chinese text found within code (comments, strings,
etc) to english. For each line containing chinese, the english translation is appended to the end of the line as a
comment.

The script runs on all files with given extensions within the specified folder and its subfolders. Each associated
output file is saved in the same folder as the input file. Its name is derived from the output file, with a prefix
and/or suffix appended.

*** ATTENTION: If neither prefix nor suffix is specified (and set to nonempty) then the original file will be replaced.
THIS IS THE DEFAULT BEHAVIOUR. ***

The script needs a local libtranslate server to be running in the background (you can use `translate_ch_en.sh` for
this).

Requirements (can be installed by running `run_once.sh`): chardet, libtranslate, libtranslatepy.
""",
                                      prog='translate_ch_en.py',)
    my_args.add_argument('--dirpath', type=str, default=path.curdir, metaver='/path/to/directory',
                         help='Folder containing files to translate (default is current directory).')
    my_args.add_argument('--extension', choices=ALL_SUPPORTED_FILE_TYPES, action='extend', required=False,
                         nargs='*', type=str,
                         help='Use this flag for each file type you want to translate. If unused, the program will ' +
                              'translate the following file types: ' + str(DEFAULT_TYPES) + '\n\nCurrently supported ' +
                              'file types: ' + str(ALL_SUPPORTED_FILE_TYPES))
    my_args.add_argument('--prefix', type=str, default='',
                         help='Prefix to add to each translated file (default is none). IF BOTH PREFIX AND SUFFIX ' +
                              'ARE EMPTY, THE ORIGINAL FILE IS REPLACED.')
    my_args.add_argument('--suffix', type=str, default='',
                         help='Suffix to add to each translated file (default is none). IF BOTH PREFIX AND SUFFIX ' +
                              'ARE EMPTY, THE ORIGINAL FILE IS REPLACED.')
    my_args.add_argument('--rawfile', type=str, default=RAW_FILE,
                         help='Output file that lists every line containing chinese. Default is `' + RAW_FILE + '` ' +
                              'and is created in the current directory.')
    my_args.add_argument('--isol_chfile', type=str, default=CH_FILE,
                         help='Output file containing isolated chinese per line. Default is `' + CH_FILE + '` and is ' +
                              'created in the current directory.')
    my_args.add_argument('--transrawfile', type=str, default=TRANS_RAW_FILE,
                         help='Output file that lists every translated line. Default is `' + TRANS_RAW_FILE + '` and ' +
                              'is created in the current directory.')
    my_args.add_argument('--listfile', type=str, default=LIST_FILE,
                         help='Output file in csv format (including header) that lists chinese, translations, and ' +
                              'corresponding line locations. Default is `' + LIST_FILE + '` and is created in the ' +
                              'current directory.')
    my_args.add_argument('--char_encoding', type=str, default=DEFAULT_ENCODING,
                         help='Expected encoding. Default is ' + DEFAULT_ENCODING + '. Input `detect` to run ' +
                              'encoding detection on each file.')
    my_parsed_args = my_args.parse_args()
    dirpath = my_parsed_args.dirpath
    if not path.isdir(dirpath):
        print('Directory '+dirpath+' does not exist. Exiting.')
    extension = my_parsed_args.extension
    if not extension:
        extension = DEFAULT_TYPES
    prefix = my_parsed_args.prefix
    suffix = my_parsed_args.suffix
    rawfile = my_parsed_args.rawfile
    chfile = my_parsed_args.isol_chfile
    transrawfile = my_parsed_args.transrawfile
    listfile = my_parsed_args.listfile
    for file in [rawfile, chfile, transrawfile, listfile]:
        folder = path.dirname(file)
        if not path.isdir(folder):
            print('Directory '+folder+' does not exist. Exiting.')
            exit(1)
    char_encoding = my_parsed_args.char_encoding
    if char_encoding != 'detect':
        lookup(char_encoding)
    translate_code(dirpath, extension, prefix, suffix, rawfile, chfile, transrawfile, listfile, char_encoding)


if __name__ == '__main__':
    standalone_cli()
