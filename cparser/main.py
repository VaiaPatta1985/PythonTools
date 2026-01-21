"""
TODO
"""

import argparse
from c_parser import parse


if __name__ == '__main__':
    my_args = argparse.ArgumentParser()
    my_args.add_argument('-i', '--input', required=True, help='input file')
    my_args.add_argument('-o', '--output', required=False, default='',
                         help='output file (default: stdout)')
    parsed_args = my_args.parse_args()
    input_file = parsed_args.input
    output_file = parsed_args.output
    parse(input_file, output_file)
