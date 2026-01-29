import re
import argparse
from os import path, walk
import chardet
from libretranslatepy import LibreTranslateAPI

LOCAL = 'http://127.0.0.1:5000/'
RAW_FILE = 'batch_raw'
CH_FILE = 'batch_ch'
TRANS_RAW_FILE = 'batch_raw_tr'
LIST_FILE = 'uncertain.csv'
CHINESE_LANGUAGE_CODE = "zh-Hans"
ENGLISH_LANGUAGE_CODE = "en"
CSV_SEPARATOR = '妈'
CSV_HEADER = CSV_SEPARATOR.join(['filename', 'line number', 'chinese', 'translation\n'])
CHINESE_PATTERN_UNICODE = r'[\u3400-\u4DBF\u4E00-\u9FFF]'
DEFAULT_ENCODING = 'utf-8'
COMMENT_START_END = {'qml': ['//', ''], 'js': ['//', ''], 'c': ['//', ''], 'cpp': ['//', ''], 'exp': ['//', ''],
                     'py': ['#', ''], 'rb': ['#', ''], 'sh': ['#', ''], 'bash': ['#', ''], 'ps1': ['#', ''],
                     'bat': ['::', ''],
                     '001': ['(*', '*)'],
                     'bas': ['\'', '']}
ALL_SUPPORTED_FILE_TYPES = COMMENT_START_END.keys()


def detect_encodings(filenames: list[str]) -> dict[str, str]:
    dict_out: dict[str, str] = {}
    for fn in filenames:
        with open(fn, "rb") as rf:
            raw = rf.read()
        dict_out[fn] = chardet.detect(raw)["encoding"]
    return dict_out


def make_raw_line_list(file_encs: dict[str, str]) -> list[list[str]]:
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
    files_found = []
    for root, dirs, files in walk(f_path):
        for file in files:
            if file.split('.')[-1].lower() in extensions:
                files_found.append(path.join(root, file))
    return files_found


def translate_code(fullpath: str, ext_in: list[str]=ALL_SUPPORTED_FILE_TYPES, pref: str='', suff: str='',
                   raw_file: str=RAW_FILE, ch_file: str=CH_FILE, trans_raw_file: str=TRANS_RAW_FILE,
                   list_file: str=LIST_FILE):
    encs = detect_encodings(get_filenames(fullpath, ext_in))
    splitlines = make_raw_line_list(encs)

    all_files_repeated: list[str] = [splitline[0] for splitline in splitlines]
    line_nums: list[str] = [splitline[1] for splitline in splitlines]
    ch_lines: list[str] = [splitline[3].removesuffix('\n') for splitline in splitlines]
    num_lines = len(splitlines)
    raw_lines = [CSV_SEPARATOR.join(splitline[0:3]) for splitline in splitlines]
    csv_lines = [CSV_HEADER]

    with open(raw_file, "w", encoding=DEFAULT_ENCODING) as out_raw_file:
        out_raw_file.writelines(raw_lines)

    for line in splitlines:
        line_to_add = line[0:2]
        line_to_add.append(line[3].removesuffix('\n'))
        csv_lines.append(CSV_SEPARATOR.join(line_to_add))

    all_files = list(set(all_files_repeated))

    print('Files have been listed.')

    with open(ch_file, "w", encoding=DEFAULT_ENCODING) as out_file:
        out_file.writelines(ch_lines)

    print('Chinese phrases have been catalogued.')

    tr_lines = [str(k) for k in range(num_lines)]
    fff = 0
    too_large: list[str] = []
    for line in ch_lines:
        if len(line) > 65000:
            too_large.append(raw_lines[fff])
        if not fff % 500:
            lt = LibreTranslateAPI(LOCAL)
        tr_lines[fff] = lt.translate(line, CHINESE_LANGUAGE_CODE, ENGLISH_LANGUAGE_CODE)
        fff = fff + 1
        print('Translated line '+str(fff)+' of '+str(num_lines)+'.')

    print('Translation has taken place.')
    print('Info on lines that are too large:')
    for itm in too_large:
        print('-------------')
        print(itm)

    for idx in range(num_lines):
        ext = all_files_repeated[idx].split('.')[-1].lower()
        if COMMENT_START_END[ext][1] and not tr_lines[idx].endswith(COMMENT_START_END[ext][1]):
            tr_lines[idx] = tr_lines[idx]+COMMENT_START_END[ext][1]
        csv_lines[idx + 1] = CSV_SEPARATOR.join([csv_lines[idx + 1], tr_lines[idx]+'\n'])

    #print(csv_lines[1])

    with open(list_file, "w", encoding=DEFAULT_ENCODING) as out_file:
        out_file.writelines(csv_lines)

    print('Changes have been listed.')

    out_lines = [raw_lines[idx].removesuffix('\n') + ' ' + \
                 COMMENT_START_END[all_files_repeated[idx].split('.')[-1].lower()][0] + tr_lines[idx] + \
                 '\n' for idx in range(num_lines)]
    with open(trans_raw_file, "w", encoding=DEFAULT_ENCODING) as f_out:
        f_out.writelines(out_lines)

    for filename in all_files:
        ext = filename.split('.')[-1].lower()
        with open(filename, "r", encoding=encs[filename]) as f_in:
            in_lines = f_in.readlines()
        rep_idx = 0
        while all_files_repeated[rep_idx] != filename:
            rep_idx = rep_idx + 1
        while all_files_repeated[rep_idx] == filename:
            in_lines[int(line_nums[rep_idx]) - 1] = \
                    in_lines[int(line_nums[rep_idx]) - 1].removesuffix('\n') + \
                    ' '+COMMENT_START_END[ext][0]+tr_lines[rep_idx]+'\n'
            rep_idx = rep_idx + 1
            if rep_idx == num_lines:
                break
        split_filename = path.split(filename)
        out_filename = split_filename[0] + pref + \
                       split_filename[1].removesuffix('.'+ext).removesuffix('.'+ext.upper()) + suff + '.' + ext
        with open(out_filename, "w", encoding=encs[filename]) as f_out:
            f_out.writelines(in_lines)


if __name__ == '__main__':
    my_args = argparse.ArgumentParser()
    my_args.add_argument('--dirpath', type=str, default=path.curdir)
    my_args.add_argument('--extension', choices=ALL_SUPPORTED_FILE_TYPES, action='append', required=False)
    my_args.add_argument('--prefix', type=str, default='')
    my_args.add_argument('--suffix', type=str, default='')
    my_args.add_argument('--rawfile', type=str, default=RAW_FILE)
    my_args.add_argument('--chfile', type=str, default=CH_FILE)
    my_args.add_argument('--transrawfile', type=str, default=TRANS_RAW_FILE)
    my_args.add_argument('--listfile', type=str, default=LIST_FILE)
    my_parsed_args = my_args.parse_args()
    dirpath = my_parsed_args.dirpath
    extension = my_parsed_args.extension
    if not extension:
        extension = ALL_SUPPORTED_FILE_TYPES
    prefix = my_parsed_args.prefix
    suffix = my_parsed_args.suffix
    rawfile = my_parsed_args.rawfile
    chfile = my_parsed_args.chfile
    transrawfile = my_parsed_args.transrawfile
    listfile = my_parsed_args.listfile
    translate_code(dirpath, extension, prefix, suffix, rawfile, chfile, transrawfile, listfile)