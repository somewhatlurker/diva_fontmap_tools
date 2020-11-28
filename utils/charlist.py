from os.path import dirname, exists as pathexists, isfile, splitext, join as joinpath, basename
from sys import argv
import json
from re import compile as re_compile
font_json_fmt_regex = re_compile(r'font(\d+)(_\d+x\d+)?\.json')

if len(argv) != 2:
    print ('Usage: {} [FONT_JSON_DIR]'.format(argv[0]))
    exit(1)

inp_path = argv[1]

if not pathexists(inp_path) or not isfile(inp_path):
    print ('Can\'t find file "{}"'.format(inp_path))
    exit(1)

with open(inp_path, 'r') as f:
    fontdata = json.load(f)

out_str = ''
for c in fontdata['chars']:
    out_str += chr(c['codepoint'])

out_path = splitext(inp_path)[0] + '_charlist.txt'

with open(out_path, 'w', encoding='utf-16') as f:
    f.write(out_str)