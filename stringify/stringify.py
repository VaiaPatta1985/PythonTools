"""
Takes a text file as input and outputs an altered copy with all the special characters escaped.
"""

import argparse
from os import path


REPLACEMENTS: dict[str, list[str]] = {'\n': ['\\n', 'LINE FEED'], '\t': ['\\t', 'HORIZONTAL TAB'],
                                      '\r': ['\\r', 'CARRIAGE RETURN'], '\0': ['\\0', 'NULL'],
                                      '\'': ['\\\'', 'SINGLE QUOTE'], '\"': ['\\\"', 'DOUBLE QUOTE'],
                                      '\v': ['\\v', 'VERTICAL TAB'], '\\': ['\\\\', 'ESCAPE CHARACTER'],}
REVERSE_REPLACEMENTS: dict[str, str] = {v[0]: k for k, v in REPLACEMENTS.items()}


def stringify_single(in_str: str, to_be_escaped: list[str]) -> str:
    out_str = in_str.replace('\\', '\\\\', -1)
    for char in to_be_escaped:
        out_str = out_str.replace(char, REPLACEMENTS[char][0], -1)
    return out_str


my_argument_parser = argparse.ArgumentParser(
    description='Takes a text file and makes an altered copy with all the special characters escaped.',
    prog='stringify',
    epilog='Characters affected:\n'+
           ', '.join([str(i + 1)+'. '+REPLACEMENTS[list(REPLACEMENTS.keys())[i]][1]
                     for i in range(len(REPLACEMENTS.keys()))]))
my_argument_parser.add_argument('input_file', type=str, help='Input file')
my_argument_parser.add_argument('--enc', type=str, required=False, default='UTF-8',
                                help='Encoding of input file (default is UTF-8)')
my_argument_parser.add_argument('--output_file', type=str, required=False, default='',
                                help='Output file (default is str_<input file>)')
my_argument_parser.add_argument('--chars_to_escape', type=str, required=False,
                                default=','.join([str(i + 1) for i in range(len(REPLACEMENTS.keys()))]),
                                help='Characters to escape (default is all characters listed). ' +
                                'Input their list indices separated by commas without spaces. ' +
                                'Escape character is always escaped.')
my_input_args = my_argument_parser.parse_args()
input_file = my_input_args.input_file
indices = [int(k) for k in my_input_args.chars_to_escape.split(',')]
indices.sort()
chars_to_escape = [list(REPLACEMENTS.keys())[k - 1] for k in indices]
if '\\' in chars_to_escape:
    chars_to_escape.remove('\\')
enc = my_input_args.enc
output_file = my_input_args.output_file
if output_file == '':
    split_file = path.split(input_file)
    output_file = split_file[0] + 'str_' + split_file[1]

with open(input_file, 'r', encoding=enc) as in_f:
    stuff = in_f.readlines()

new_stuff: list[str] = []
for line in stuff:
    new_stuff.append(stringify_single(line, chars_to_escape))

with open(output_file, 'w', encoding=enc) as out_f:
    out_f.writelines(new_stuff)
