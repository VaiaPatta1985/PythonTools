"""
Takes a C file as input, tokenises C syntax and outputs results to json.
Based on Kornelius Kalnbach's Coderay, and specifically this source file:
https://github.com/rubychan/coderay/blob/b5b3430d4635682b767c44469e28a70fe234187e/lib/coderay/scanners/c.rb
Their code used in compliance with MIT license, which Coderay was published under:
https://github.com/rubychan/coderay/blob/228e87307c2faab06f854a79ab592a2737c20f65/MIT-LICENSE
"""


# Packages
from enum import Enum
import re
from typing import NamedTuple
import argparse
import json


# Classes
State = Enum('State', ['INITIAL', 'STRING', 'INCLUDE_EXPECTED'])
TokenType = Enum('TokenType', ['TEXT', 'BLOCK'])
Action = Enum('Action', ['OPEN', 'BEGIN_LINE', 'CLOSE', 'END_LINE', 'NONE'])
Kind = Enum('Kind', ['IDENT',  # unidentified
                     'KEYWORD', 'DIRECTIVE', 'PREDEFINED_TYPE', 'PREDEFINED_CONSTANT',  # reserved words
                     'LABEL',  # case of switch statement
                     #'ERROR',
                     'MODIFIER', 'DELIMITER', 'PREPROCESSOR', 'CHAR', 'HEX', 'OCTAL', 'INTEGER', 'FLOAT',
                     'STRING', 'SPACE', 'COMMENT', 'OPERATOR', 'CONTENT', 'INCLUDE'])
Token = NamedTuple('Token', [('token_type', TokenType), ('action', Action), ('text', str), ('kind', Kind)])


# Helper functions
def one_of(reg1: re.Pattern, reg2: re.Pattern, flags: re.RegexFlag=re.NOFLAG) -> re.Pattern:
    """
    Regex that matches both given patterns.
    Ignores original regex flags of each input pattern.
    Optionally specify flags for output pattern.
    :param reg1: first regex pattern
    :param reg2: second regex pattern
    :param flags: output regex flags
    :return: pattern to the effect of ["reg1 or reg2", flags]
    """
    return re.compile(r'(?:(' + reg1.pattern + r')|(' + reg2.pattern + r'))', flags)


def pattern_compose(reg1: re.Pattern, reg2: re.Pattern, flags: re.RegexFlag=re.NOFLAG) -> re.Pattern:
    """
    Regex that matches the sequence of input patterns in the given order.
    Ignores original regex flags of each input pattern.
    Optionally specify flags for output pattern.
    :param reg1: first regex pattern
    :param reg2: second regex pattern
    :param flags: output regex flags
    :return: pattern to the effect of ["reg1 reg2", flags]
    """
    return re.compile(reg1.pattern + reg2.pattern, flags)


def zero_or_one(reg: re.Pattern) -> re.Pattern:
    """
    Regex that matches the given pattern or the empty pattern.
    Retains original regex flags of input pattern.
    :param reg: regex pattern
    :return: pattern to the effect of "reg1?"
    """
    return re.compile(r'(' + reg.pattern + r')?', reg.flags)


# Constant objects
SECONDARY_PATTERNS: dict[str, re.Pattern] = {
    'LABEL': re.compile(r':(?!:)'),
    'PREPROCESSOR_IF_SUBBLOCK_END': re.compile(r'^\# (?:elif|else|endif) .*? $ | \Z', re.MULTILINE),
    'COMMAND_BLOCK': re.compile(r'[;\{\}]'),
}
ESCAPE = one_of(re.compile(r'[rbfntv\n\\' + r"'" + r'"]'), re.compile(r'x[a-fA-F0-9]{1,2}|[0-7]{1,3}'))
ESCAPED_ESCAPE = pattern_compose(re.compile(r'\\'), ESCAPE)
UNICODE_ESCAPE = re.compile(r'u[a-fA-F0-9]{4}|U[a-fA-F0-9]{8}')
MAIN_PATTERNS_INITIAL_STATE: dict[str, re.Pattern] = {
    'WHITESPACE': re.compile(r'\s+ | \\\n'),
    'COMMENT_GENERAL': re.compile(r'// [^\n\\]* (?: \\. [^\n\\]* )* | /\* (?: .*? \*/ | .* )'),
    'OPERATOR': re.compile(r'[-+*=<>?:;,!&^|()\[\]{}~%]+ | \/=? | \.(?!\d)'),
    'ALPHANUMERIC_STARTING_WITH_LETTER': re.compile(r'[A-Za-z_][A-Za-z_0-9]*'),
    'STRING': re.compile(r'[:alpha:]?"'),
    'PREPROCESSOR_IF_SUBBLOCK_BEGIN': re.compile(r'\# \s* if \s* 0'),
    'PREPROCESSOR_INSTRUCTION': re.compile(r'#[ \t]*(\w*)'),
    'CHAR': pattern_compose(re.compile(r"[:alpha:]?'"),
                            pattern_compose(zero_or_one(one_of(re.compile(r"[^\'\n\\]"), ESCAPED_ESCAPE)),
                                            re.compile(r"'?"))),
    'IDENT': re.compile(r'\$'),
    'HEX': re.compile(r'0[xX][0-9A-Fa-f]+'),
    'OCTAL': re.compile(r'(?:0[0-7]+)(?![89.eEfF])'),
    'INTEGER': re.compile(r'(?:\d+)(?![.eEfF])[:alpha:]?[:alpha:]?'),
    'FLOAT': re.compile(r'\d[fF]?|\d*\.\d+(?:[eE][+-]?\d+)?[fF]?|\d+[eE][+-]?\d+[fF]?'),
}
MAIN_PATTERNS_STRING_STATE: dict[str, re.Pattern] = {
    'CONTENT': re.compile(r'[^\\\n"]+'),
    'STRING_DELIMITER': re.compile(r'"'),
    'TEXT_CHAR': pattern_compose(re.compile(r'\\'), one_of(ESCAPE, UNICODE_ESCAPE)),
    #'STRING_IN_BLOCK': re.compile(r'\\ | $'),
}
MAIN_PATTERNS_INCLUDE_EXPECTED_STATE: dict[str, re.Pattern] = {
    'INCLUDE': re.compile(r'<[^>\n]+>?|"[^"\n\\]*(?:\\.[^"\n\\]*)*"?'),
    'SPACE': re.compile(r'\s+'),
}
STATES_AND_PATTERNS: dict[State, dict[str, re.Pattern]] = {
    State.INITIAL: MAIN_PATTERNS_INITIAL_STATE,
    State.STRING: MAIN_PATTERNS_STRING_STATE,
    State.INCLUDE_EXPECTED: MAIN_PATTERNS_INCLUDE_EXPECTED_STATE,
}
KEYWORDS: tuple[str] = ('asm', 'break', 'case', 'continue', 'default', 'do', 'else', 'enum', 'for', 'goto', 'if',
                        'return', 'sizeof', 'struct', 'switch', 'typedef', 'union', 'while', 'restrict')
DIRECTIVES: tuple[str] = ('auto', 'extern', 'register', 'static', 'void', 'const', 'volatile', 'inline')
PREDEFINED_TYPES: tuple[str] = ('int', 'long', 'short', 'char', 'signed', 'unsigned', 'float', 'double', 'bool',
                                'complex')
PREDEFINED_CONSTANTS: tuple[str] = ('EOF', 'NULL', 'true', 'false')
TUPLE_TO_KIND: dict[tuple[str], Kind] = {KEYWORDS: Kind.KEYWORD,
                                         DIRECTIVES: Kind.DIRECTIVE,
                                         PREDEFINED_TYPES: Kind.PREDEFINED_TYPE,
                                         PREDEFINED_CONSTANTS: Kind.PREDEFINED_CONSTANT}
KINDS_OF_RESERVED_WORDS = TUPLE_TO_KIND.keys()


# Core function
def scan_tokens(input_string: str) -> list[Token]:
    """
    Takes the source code as input and outputs a list of syntactic elements and their properties.
    Corresponds to the `scan_tokens` method in file `c.rb` of the Coderay repository.
    :param input_string: the entire content of the C source file
    :return: a list of Tokens, each a tuple comprising the following elements:
     token type (enum): either text or block;
     action (enum): open, close, begin line, end line, or none;
     text (str): usually the corresponding text from the source code;
     kind (enum): whether the parsed text is a keyword, an integer, a comment, etc
                  (see Kind enum for the full list)
    """
    state = State.INITIAL
    label_expected = True
    case_expected = False
    label_expected_before_preproc_line = False
    in_preproc_line = False
    tokens: list[Token] = []
    input_length = len(input_string)
    position = 0
    pattern = None
    main_patterns = STATES_AND_PATTERNS[state]
    while position < input_length:
        regex_match = None
        previous_position = position
        while regex_match is None:
            for pattern in main_patterns.values():
                regex_match = pattern.fullmatch(input_string[previous_position:position])
                if regex_match is not None:
                    break
            position += 1
        tentative_regex_match = regex_match
        new_position = position
        while tentative_regex_match is not None:
            regex_match = tentative_regex_match
            position = new_position
            new_position += 1
            tentative_regex_match = pattern.fullmatch(input_string[previous_position:new_position])

        print(pattern)  # debugging
        print(regex_match[0])
        match state:
            case State.INITIAL:
                if pattern == main_patterns['WHITESPACE']:
                    if in_preproc_line and regex_match[0] != '\\\n' and regex_match[0].find('\n') > -1:
                        in_preproc_line = False
                        label_expected = label_expected_before_preproc_line
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.SPACE))
                elif pattern == main_patterns['COMMENT_GENERAL']:
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.COMMENT))
                elif pattern == main_patterns['OPERATOR']:
                    label_expected = SECONDARY_PATTERNS['COMMAND_BLOCK'].match(regex_match[0]) is not None
                    if case_expected:
                        if regex_match[0] == ':':
                            label_expected = True
                        case_expected = False
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.OPERATOR))
                elif pattern == main_patterns['ALPHANUMERIC_STARTING_WITH_LETTER']:
                    current_kind = Kind.IDENT
                    for kind in KINDS_OF_RESERVED_WORDS:
                        if regex_match[0] in kind:
                            current_kind = TUPLE_TO_KIND[kind]
                            break
                    if current_kind == Kind.IDENT and label_expected and not in_preproc_line:
                        tentative_regex_match = regex_match
                        new_position = position
                        # Disambiguation note:
                        # `old_position` is the value of `position` before we change it within the *same* loop
                        # `previous_position` is the value of `position` from the *previous* loop
                        old_position = position
                        while tentative_regex_match is not None:
                            regex_match = tentative_regex_match
                            position = new_position
                            new_position += 1
                            tentative_regex_match = \
                                SECONDARY_PATTERNS['LABEL'].fullmatch(input_string[previous_position:new_position])
                        if old_position == position:
                            label_expected = False
                        else:
                            current_kind = Kind.LABEL
                    else:
                        label_expected = False
                    if not label_expected and regex_match[0] in ['case', 'default']:
                            case_expected = True
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=current_kind))
                elif pattern == main_patterns['STRING']:
                    tokens.append(Token(token_type=TokenType.BLOCK, action=Action.OPEN, text='', kind=Kind.STRING))
                    if regex_match[0].isalpha():
                        tokens.append(
                            Token(token_type=TokenType.TEXT, action=Action.NONE, text='L', kind=Kind.MODIFIER))
                        regex_match[0] = '\"'
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.DELIMITER))
                    state = State.STRING
                elif pattern == main_patterns['PREPROCESSOR_IF_SUBBLOCK_BEGIN']:
                    content = ''
                    content_end = position
                    content_match = None
                    if position < input_length:
                        while content_match is None:
                            content_end += 1
                            content = input_string[position:content_end]
                            content_match = SECONDARY_PATTERNS['PREPROCESSOR_IF_SUBBLOCK_END'].search(content)
                        regex_match[0] = regex_match[0] + content
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.COMMENT))
                elif pattern == main_patterns['PREPROCESSOR_INSTRUCTION']:
                    tokens.append(Token(
                        token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.PREPROCESSOR))
                    in_preproc_line = True
                    label_expected_before_preproc_line = label_expected
                    if regex_match[1] == 'include':
                        state = State.INCLUDE_EXPECTED
                elif pattern == main_patterns['CHAR']:
                    label_expected = False
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.CHAR))
                elif pattern == main_patterns['IDENT']:
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.IDENT))
                elif pattern == main_patterns['HEX']:
                    label_expected = False
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.HEX))
                elif pattern == main_patterns['OCTAL']:
                    label_expected = False
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.OCTAL))
                elif pattern == main_patterns['INTEGER']:
                    label_expected = False
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.INTEGER))
                elif pattern == main_patterns['FLOAT']:
                    label_expected = False
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.FLOAT))
                else:
                    raise Exception()
                    #tokens.append(Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.ERROR))
            case State.STRING:
                if pattern == main_patterns['CONTENT']:
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.CONTENT))
                elif pattern == main_patterns['STRING_DELIMITER']:
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.DELIMITER))
                    tokens.append(Token(token_type=TokenType.BLOCK, action=Action.CLOSE, text='', kind=Kind.STRING))
                    state = State.INITIAL
                    label_expected = False
                elif pattern == main_patterns['TEXT_CHAR']:
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.CHAR))
#                elif pattern == main_patterns['STRING_IN_BLOCK']:
#                    tokens.append(Token(token_type=TokenType.BLOCK, action=Action.CLOSE, text='', kind=Kind.STRING))
#                    tokens.append(Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.ERROR))
#                    state = State.INITIAL
#                    label_expected = False
                else:
                    raise Exception()
            case State.INCLUDE_EXPECTED:
                if pattern == main_patterns['INCLUDE']:
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.INCLUDE))
                    state = State.INITIAL
                elif pattern == main_patterns['SPACE']:
                    tokens.append(
                        Token(token_type=TokenType.TEXT, action=Action.NONE, text=regex_match[0], kind=Kind.SPACE))
                    if regex_match[0].find('\n') > -1:
                        state = State.INITIAL
                else:
                    state = State.INITIAL
            case _:
                raise Exception()

    if state == State.STRING:
        tokens.append(Token(token_type=TokenType.BLOCK, action=Action.END_LINE, text='', kind=Kind.STRING))
    return tokens


# Main function
def parse(c_file: str, jsn: str) -> None:
    """
    This is the entry point to use cparser as a tool.
    It is the main function, which takes a C source file,
    calls `scan_tokens` to get a `Token` list, and outputs
    the result as json, either to a file or to `stdout`.
    The `Token` class is a named tuple (see definition above).
    :param c_file: file containing C code
    :param jsn: output file (omit or use empty string to use stdout)
    :return: None
    """
    with open(c_file, 'r') as sourcefile:
        c_code = sourcefile.read()
    token_list = scan_tokens(c_code)
    if jsn:
        json.dump(token_list, open(jsn, 'w'))
    else:
        print(json.dumps(token_list))


# Library guard
if __name__ == '__main__':
    my_args = argparse.ArgumentParser()
    my_args.add_argument('-i', '--input', required=True, help='input file')
    my_args.add_argument('-o', '--output', required=False, default='',
                         help='output file (default: stdout)')
    parsed_args = my_args.parse_args()
    input_file = parsed_args.input
    output_file = parsed_args.output
    parse(input_file, output_file)
