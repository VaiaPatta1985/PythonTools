"""
Takes a text file and makes an altered copy with all the special characters escaped.
"""

import argparse
from os import path


REPLACEMENTS: dict[str, str] = {'\n': '\\n', '\t': '\\t', '\r': '\\r', '\0': '\\0', '\'': '\\\'', '\"': '\\\"',}
REVERSE_REPLACEMENTS: dict[str, str] = {v: k for k, v in REPLACEMENTS.items()}


def stringify_single(in_str: str, to_be_escaped: list[str]) -> str:
    out_str = in_str.replace('\\', '\\\\', -1)
    for char in to_be_escaped:
        out_str = out_str.replace(char, REPLACEMENTS[char], -1)
    return out_str


my_argument_parser = argparse.ArgumentParser(
    description='Takes a text file and makes an altered copy with all the special characters escaped.',
    prog='stringify', epilog='Characters affected: '+','.join(list(REPLACEMENTS.values())))  # usage='', )
my_argument_parser.add_argument('input_file', type=str, help='Input file')
my_argument_parser.add_argument('-enc', type=str, required=False, default='UTF-8',
                                help='Encoding of input file (default is UTF-8)')
my_argument_parser.add_argument('-output_file', type=str, required=False, default='',
                                help='Output file (default is str_<input file>)')
my_input_args = my_argument_parser.parse_args()
input_file = my_input_args.input_file
chars_to_escape = list(REPLACEMENTS.keys())
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
