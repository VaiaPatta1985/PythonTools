"""
Takes a C file as input, parses C syntax and outputs results to json.
"""

import argparse
import json


def c_to_json(c_file: str) -> json:
    pass


def parse(c_code: str, jsn: str) -> None:
    blob = c_to_json(c_code)
    if jsn:
        json.dump(blob, open(jsn, "w"))
    else:
        print(json.dumps(blob))


if __name__ == '__main__':
    my_args = argparse.ArgumentParser()
    my_args.add_argument('-i', '--input', required=True, help='input file')
    my_args.add_argument('-o', '--output', required=False, default='',
                         help='output file (default: stdout)')
    parsed_args = my_args.parse_args()
    input_file = parsed_args.input
    output_file = parsed_args.output
    parse(input_file, output_file)
