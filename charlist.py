from os.path import exists as pathexists, isfile, splitext
from sys import argv, exit
import json

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
    ch = c['codepoint']
    if ch >= 0xd800 and ch <= 0xdfff:
        print ('Ignoring invalid codepoint: 0x{:04x}'.format(ch))
    else:
        out_str += chr(ch)

out_path = splitext(inp_path)[0] + '_charlist.txt'

with open(out_path, 'w', encoding='utf-16') as f:
    f.write(out_str)