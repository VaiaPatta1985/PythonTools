# assembly_made_easy.py
"""
Write x86-64 Assembly (NASM, ABI System V) like a boss. Write your program using comprehensible variable names instead
of register names like 'r10' or 'xmm5'.

For more information on function and usage, call this script using the `-h` parameter on the command line.
"""


import argparse
import re
from os import path
from enum import Enum


Errors = Enum('Errors', [
    'SUCCESS', 'CANNOT_FIND_FUNCTION', 'CANNOT_FIND_RETURN', 'CANNOT_FIND_INPUT_FILE', 'CANNOT_FIND_LIBRARY_FILE',
    'CANNOT_FIND_OUTPUT_DIRECTORY'
], start=0)


ERROR_MESSAGES: dict[Errors, str] = {
    Errors.SUCCESS: 'Done.',
    Errors.CANNOT_FIND_FUNCTION: 'Cannot find function.',
    Errors.CANNOT_FIND_RETURN: 'Cannot find return instruction.',
    Errors.CANNOT_FIND_INPUT_FILE: 'Could not find input file.',
    Errors.CANNOT_FIND_LIBRARY_FILE: 'Could not find library file.',
    Errors.CANNOT_FIND_OUTPUT_DIRECTORY: 'Could not find directory of output file.',
}

REGISTER64 = ['rax', 'rbx', 'rcx', 'rdx', 'rdi', 'rsi', 'rsp', 'rbp',
              'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15']

REGISTER128 = ['xmm0', 'xmm1', 'xmm2', 'xmm3', 'xmm4', 'xmm5', 'xmm6', 'xmm7',
               'xmm8', 'xmm9', 'xmm10', 'xmm11', 'xmm12', 'xmm13', 'xmm14', 'xmm15']

ALL_REGISTERS = REGISTER64 + REGISTER128


def get_global_register_aliases(input_file: str|None) -> dict[str, list[str]]:
    """
    Scans input file `input_file` for lines of the form '%define A B [;comment]', where B is a register (ie contained in
    `ALL_REGISTERS`), and returns a dict mapping each register to a list of its aliases. When not given a file to scan,
    all values of the dict are an empty list.

    Caveat: If you write '%define alias0 rax' on one line and then '%define alias1 alias0' on a later line, alias1 won't
    be included in the dict. You have to write it as '%define alias1 rax'.

    Parameters:
        input_file (str|None): File to scan for the defines of register aliases.
    Returns:
        result (dict[str, list[str]]): A mapping from each register to a list of its aliases.
    """
    result: dict[str, list[str]] = {r: [] for r in ALL_REGISTERS}
    if input_file:
        with open(input_file, 'r') as f:
            lines = f.readlines()
        for line in lines:
            line_words = line.split(';')[0].split(' ')
            while '' in line_words:
                line_words.remove('')
            if line_words:
                line_words[-1] = line_words[-1].removesuffix('\n')
            if len(line_words) == 3:
                if line_words[0] == '%define' and line_words[2] in ALL_REGISTERS:
                    result[line_words[2]].append(line_words[1])
    return result


def distinct_word_but_not_in_double_curly_brackets(word: str) -> re.Pattern:
    """
    Given the string `word` (eg 'test'), this function returns a regular expression pattern which:
        - does not match strings that do not contain 'test';
        - does not match 'blahblahtest', 'blahblahtestblahblah', '_test0', or any other string where 'test' appears
          concatenated with letters, digits, or underscores;
        - does not match '{{test}}';
        - matches 'blahblah test blahblah', 'blahblah:test;blahblah', 'blah test', and any other string where 'test'
          appears as a distinct word, as long as it isn't within double curly brackets (as in '{{test}}').
    Parameters:
        word (str): The word to be matched by the pattern (except if contained in curly brackets).
    Returns:
        (re.Pattern): A regular expression pattern that behaves as described above.
    """
    pattern = '(?:[^{]{{1}|[^{_0-9a-zA-Z]|^)' + word + '(?:}{1}[^}]|[^}_0-9a-zA-Z]|$)|(?:{{)' + word + \
              '}{1}[^}]|[^{]{{1}' + word + '(?:}})'
    return re.compile(pattern)


def record_aliases_and_remove_brackets(bracketed: str, line: str) -> tuple[str, list[str]]:
    """
    This function looks for instances of '{{`bracketed`}}' within string `line`, removes these substrings from `line`,
    and adds the word preceding '{{`bracketed`}}' to the lists `first_list` and `second_list`.
    Parameters:
        bracketed (str): To search for '{{`bracketed`}}'.
        line (str): String to search.
    Returns:
        Updated `line`;
        list of words preceding instances of '{{`bracketed`}}'.
    """
    preceding_words = []
    while line.find('{{' + bracketed + '}}') != -1:
        words = line[0:line.find('{{' + bracketed + '}}')].split(' ')
        while '' in words:
            words.remove('')
        alias = words[-1]
        preceding_words.append(alias)
        line = line.replace('{{' + bracketed + '}}', '', 1)
    return line, preceding_words


def find_function_start_end(lines: list[str], assembly_function: str) -> tuple[int, int, Errors]:
    """
    Looks for function with name `assembly_function` within code lines `lines` and returns the positions of its first
    and last line, starting from 0 (position value is -1 if not found). It also returns an error code, member of the
    `Errors` Enum, which is the 0-valued `Errors.SUCCESS` if both positions were found and a nonzero code otherwise
    (`Errors.CANNOT_FIND_FUNCTION` if the start cannot be found; `Errors.CANNOT_FIND_RETURN` if the start was found but
    the end cannot be found).

    The value of the error code can be used by the caller as an exit value. The error codes are also keys to the
    `ERROR_MESSAGES` dict, where the value corresponding to each error code is an appropriate error message.
    Parameters:
        lines (list[str]): Lines of assembly code.
        assembly_function (str): Name of the assembly function.
    Returns:
        Position of first line in the assembly function, starting from 0 (position value is -1 if not found);
        position of last line in the assembly function, starting from 0 (position value is -1 if not found);
        error code (can be 0-valued to indicate success).
    """
    error = Errors.SUCCESS
    start_function = -1
    end_function = -1
    for line_num in range(len(lines)):
        content = lines[line_num].split(';')[0].strip()
        if content.endswith(':') and content.removesuffix(':').strip() == assembly_function:
            start_function = line_num + 1
            break
    if start_function == -1:
        error = Errors.CANNOT_FIND_FUNCTION
    else:
        for line_num in range(start_function, len(lines)):
            content = lines[line_num].split(';')[0].strip()
            if content == 'ret':
                end_function = line_num
                break
        if end_function == -1:
            error = Errors.CANNOT_FIND_RETURN
    return start_function, end_function, error


def make_it_easy(input_file: str, output_file: str, function_list: list[str], library_file: str|None) -> Errors:
    """
    This function is where all the magic happens. After getting global register aliases from the library file
    `library_file`, it reads the 'easy assembly' file `input_file` and, for each assembly function on the assembly
    function list `function_list`, it records occurrences of register names (or their global aliases) both in the code
    and in double curly brackets. It then creates the output file `output_file` with assembly code as in the input, but
    with the bracketed expressions deleted, and a 'define-undef pair' for each bracketed expression. Concretely, each
    expression of the form 'alias{{register}}' produces a '%define alias register' at the beginning of the function and
    an '%undef alias' at the end of the function. Moreover, a warning comment is added for each register that appears
    under more than one name/alias in the function.

    The function returns an error code, member of the `Errors` Enum, which is either the 0-valued `Errors.SUCCESS` if
    all goes well or a nonzero code signifying that an assembly function in the function list cannot be found. The value
    of the error code can be used by the caller as an exit value. The error codes are also keys to the `ERROR_MESSAGES`
    dict, where the value corresponding to each error code is an appropriate error message.
    Parameters:
        input_file (str): File containing 'easy assembly' code.
        output_file (str): File to contain final assembly code.
        function_list (list[str]): List of functions to be processed.
        library_file (str|None): File containing library with defines of global register aliases.
    Returns:
        Error code. Can be 0-valued to indicate success.
    """
    register_global_aliases = get_global_register_aliases(library_file)
    register_names_and_global_aliases = {reg: register_global_aliases[reg] + [reg] for reg in ALL_REGISTERS}
    # appearance_of maps each register name or global alias to the pattern detecting
    # its appearance as a distinct word but not in {{...}}
    appearance_of: dict[str, re.Pattern] = {}
    for register in ALL_REGISTERS:
        for register_name_or_global_alias in register_names_and_global_aliases[register]:
            appearance_of[register_name_or_global_alias] = \
              distinct_word_but_not_in_double_curly_brackets(register_name_or_global_alias)

    with open(input_file, 'r') as f:
        lines = f.readlines()

    for assembly_function in function_list:
        print('Defining local register aliases for function ' + assembly_function + '...')
        # `local_aliases` will contain a list of local aliases corresponding to each register
        local_aliases: dict[str, list[str]] = {reg: [] for reg in ALL_REGISTERS}
        # `aliases_and_names` will contain a list of all aliases of each register, including its name
        aliases_and_names: dict[str, list[str]] = {reg: [] for reg in ALL_REGISTERS}
        start_function, end_function, error = find_function_start_end(lines, assembly_function)
        if error.value:
            return error
        for line_num in range(start_function, end_function):
            line0 = lines[line_num].split(';')[0].strip()
            # record appearances of registers and their global aliases in actual assembly code (ie not bracketed)
            for register in ALL_REGISTERS:
                for register_name_or_global_alias in register_names_and_global_aliases[register]:
                    if appearance_of[register_name_or_global_alias].search(line0):
                        aliases_and_names[register].append(register_name_or_global_alias)
            # record local aliases and remove brackets
            if line0.find('{{') != -1:
                line = line0
                for register in ALL_REGISTERS:
                    for register_name_or_global_alias in register_names_and_global_aliases[register]:
                        line, alias_list = record_aliases_and_remove_brackets(register_name_or_global_alias, line)
                        local_aliases[register] += alias_list
                        aliases_and_names[register] += alias_list
                lines[line_num] = lines[line_num].replace(line0, line, 1)
        # get rid of multiple entries in each list
        for register in ALL_REGISTERS:
            aliases_and_names[register] = list(set(aliases_and_names[register]))
            local_aliases[register] = list(set(local_aliases[register]))
        # warning comment for reused registers
        reused_registers = [r for r in ALL_REGISTERS if len(aliases_and_names[r]) > 1]
        if reused_registers:
            lines.insert(start_function,
                         '; CAUTION! The following registers are reused with different aliases:\n')
            start_function += 1
            end_function += 1
            for register in reused_registers:
                lines.insert(start_function, '; ' + register + ': ' + ', '.join(aliases_and_names[register]) + '\n')
                start_function += 1
                end_function += 1
        # add defines and undefs to code
        for register, names in local_aliases.items():
            for name in names:
                lines.insert(start_function, '%define ' + name + ' ' + register + '\n')
                start_function += 1
                end_function += 1
                lines.insert(end_function, '%undef ' + name + '\n')
                end_function += 1

    with open(output_file, 'w') as f:
        f.writelines(lines)

    return Errors.SUCCESS


def standalone_cli() -> Errors:
    """
    This function does the parsing of command line arguments, checks their validity, and passes them on to the function
    that does most of the processing (`make_it_easy`).

    It returns an error code, member of the `Errors` Enum, which is
    either the 0-valued `Errors.SUCCESS` if all goes well or a nonzero code signifying an error. The value of the error
    code can be used by the caller as an exit value. The error codes are also keys to the `ERROR_MESSAGES` dict, where the
    value corresponding to each error code is an appropriate error message.

    For CLI information, use the `-h` parameter on the command line.
    Returns:
        (Errors): Error code. Can be 0-valued to indicate success.
    """
    my_args = argparse.ArgumentParser(add_help=True, formatter_class=argparse.RawDescriptionHelpFormatter,
                                      prog='assembly_made_easy.py', description="""
Aid for writing x86-64 Assembly (NASM, ABI System V).

Write your Assembly functions using proper variable names (to be defined per function) in place of register names. The
first time you use each alias, put the register name in double curly brackets next to it (eg `mov result{{rax}}, 1`).
Don't use spaces inside the brackets. Subsequently you can just write the alias (eg `inc result`).

Save your file, then use this program to automatically produce all the boring defines and undefines (and delete the
bracketed register names). For the preceding example, the line `%define result rax` will be added at the beginning of
the function, the line `%undef result` will be added at the end of the function, and `mov result{{rax}}, 1` will be
replaced by `mov result, 1`. A warning comment will be added to the code whenever a register is reused under a different
alias within the same function.

The program also recognises the register aliases from a given macros library (it doesn't check if you've included it in
your assembly file). These are aliases to be used globally, and the program records which register they refer to, so
they can be used to define local aliases (eg if the library file contains `%define output rax` then you can write
`mov result{{output}}, 1`).

The program doesn't check if the characters ';', '{', and '}' are in a string, so in that case you should replace them
with their respective ASCII codes (ie 59, 123, and 125).
""")
    my_args.add_argument('input', help='Your \'easy assembly\' file.')
    my_args.add_argument('-o', '--output', required=False,
                         help='Name of the final assembly file. Default is to alter the input in-place.')
    my_args.add_argument('-f', '--function', '--functions', required=True, action='append', nargs='+',
                         metavar='function', help='Names of the functions that contain register aliases.')
    my_args.add_argument('-l', '--library', required=False,
                         help='Name of a library file that contains global aliases for registers. ' +
                              '(Anything that is defined as a register within will be considered a global alias.)')
    my_parsed_args = my_args.parse_args()
    input_file = my_parsed_args.input
    if not path.isfile(input_file):
        return Errors.CANNOT_FIND_INPUT_FILE
    output_file = my_parsed_args.output
    function_list_list = my_parsed_args.function
    function_list = []
    for fun_list in function_list_list:
        for fun in fun_list:
            function_list.extend(fun.split(','))
    while '' in function_list:
        function_list.remove('')
    function_list = list(set(function_list))
    library_file = my_parsed_args.library
    if library_file and not path.isfile(library_file):
        return Errors.CANNOT_FIND_LIBRARY_FILE
    if not output_file:
        output_file = input_file
    elif path.dirname(output_file) and not path.isdir(path.dirname(output_file)):
        return Errors.CANNOT_FIND_OUTPUT_DIRECTORY
    return make_it_easy(input_file, output_file, function_list, library_file)


# Library guard
if __name__ == '__main__':
    overall_result = standalone_cli()
    print(ERROR_MESSAGES[overall_result])
    exit(overall_result.value)
