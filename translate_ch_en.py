from libretranslatepy import LibreTranslateAPI

LOCAL = 'http://127.0.0.1:5000/'
IN_FILE = 'batch_raw'
CH_FILE = 'batch_ch'
LIST_FILE = 'uncertain.csv'
CSV_SEPARATOR = '妈'

with open(IN_FILE, "r") as in_file:
    lines = in_file.readlines()

print(IN_FILE+' has been read.')

num_lines = len(lines)

all_files_repeated: list[str] = []
csv_lines = ['filename'+CSV_SEPARATOR+'line number'+CSV_SEPARATOR+'chinese'+CSV_SEPARATOR+'translation\n']
rest_of_line: list[str] = []
line_nums: list[str] = []

for line in lines:
    split_line = line.split(':')
    all_files_repeated.append(split_line[0])
    line_nums.append(split_line[1])
    rest_of_line.append(''.join(split_line[2:len(split_line)]))
    csv_lines.append(CSV_SEPARATOR.join(split_line[0:2]))

all_files = list(set(all_files_repeated))

print('Files have been listed.')

with open(CH_FILE, "r") as in_file:
    ch_lines = in_file.readlines()

print('Chinese phrases have been catalogued.')

tr_lines = [str(k) for k in range(num_lines)]
fff = 0
too_large: list[str] = []
for line in ch_lines:
    if len(line) > 65000:
        too_large.append(lines[fff])
    if not fff % 500:
        lt = LibreTranslateAPI(LOCAL)
    tr_lines[fff] = lt.translate(line.removesuffix('\n'), "zh-Hans", "en")
    fff = fff + 1
    print('Translating line '+str(fff)+' of '+str(num_lines)+'.')

print('Translation has taken place.')
print('Info on lines that are too large:')
for itm in too_large:
    print('-------------')
    print(itm)

for idx in range(num_lines):
    if all_files_repeated[idx].endswith('.001') and \
       not tr_lines[idx].endswith('*)'):
        tr_lines[idx] = tr_lines[idx]+'*)'
    csv_lines[idx + 1] = \
        CSV_SEPARATOR.join([csv_lines[idx + 1], ch_lines[idx].removesuffix('\n'),
                            tr_lines[idx]+'\n'])

#print(csv_lines[1])

with open(LIST_FILE, "w") as out_file:
    out_file.writelines(csv_lines)

print('Changes have been listed.')

out_lines: list[str] = []
with open(IN_FILE, "r") as f_in:
    in_lines = f_in.readlines()
    for idx in range(num_lines):
        out_lines.append(
            in_lines[idx].removesuffix('\n')+' //'+tr_lines[idx]+'\n')
with open(IN_FILE+'_tr', "w") as f_out:
    f_out.writelines(out_lines)

for filename in all_files:
    with open(filename, "r") as f_in:
        in_lines = f_in.readlines()
    rep_idx = 0
    while all_files_repeated[rep_idx] != filename:
        rep_idx = rep_idx + 1
    while all_files_repeated[rep_idx] == filename:
        if filename.endswith('.001'):
            in_lines[int(line_nums[rep_idx]) - 1] = \
                in_lines[int(line_nums[rep_idx]) - 1].removesuffix('\n') + \
                ' (*'+tr_lines[rep_idx]+'\n'
        else:
            in_lines[int(line_nums[rep_idx]) - 1] = \
                in_lines[int(line_nums[rep_idx]) - 1].removesuffix('\n') + \
                ' //'+tr_lines[rep_idx]+'\n'
        rep_idx = rep_idx + 1
        if rep_idx == num_lines:
            break
    with open(filename+'_tr', "w") as f_out:
        f_out.writelines(in_lines)
