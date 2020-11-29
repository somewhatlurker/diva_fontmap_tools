from os.path import dirname, exists as pathexists, isfile, splitext, join as joinpath, basename
from os import listdir, mkdir, remove as removefile
from sys import argv
from re import compile as re_compile
import json
import pyfmh3
import pyfarc


font_json_fmt = 'font{}_{}x{}.json'
font_json_fmt_regex = re_compile(r'font(\d+)(_\d+x\d+)?\.json$')

fontmap_magic = ['FMH3', 'FONM']


def fmh3_from_farc_stream(f):
    farc = pyfarc.from_stream(f)
    for fname, finfo in farc['files'].items():
        data = finfo['data']
        if data[:4].decode('ascii') in fontmap_magic:
            return pyfmh3.from_bytes(data)
    
    raise Exception('Couldn\'t find fontmap in farc')

def clean_dir(d):
    files = listdir(d)
    
    for f in files:
        if font_json_fmt_regex.match(f):
            removefile(joinpath(d, f))


if len(argv) != 2:
    print ('Usage: {} [FMH3_FILE|FONT_JSON_DIR]'.format(argv[0]))
    exit(1)

inp_path = argv[1]

if not pathexists(inp_path):
    print ('Can\'t find file or directory "{}"'.format(inp_path))
    exit(1)


if isfile(inp_path):
    print ('Extracting "{}" to directory'.format(inp_path))
    
    with open(inp_path, 'rb') as f:
        magic = f.read(4).decode('ascii')
        f.seek(0)
        
        if magic in fontmap_magic:
            fmh = pyfmh3.from_stream(f)
        else:
            try:
                pyfarc.check_farc_type(magic)
                fmh = fmh3_from_farc_stream(f)
            except Exception as e:
                print (e)
                exit(1)
    
    out_dir = inp_path
    while '.' in basename(out_dir):
        out_dir = splitext(out_dir)[0]
    
    if pathexists(out_dir):
        clean_dir(out_dir)
    else:
        mkdir(out_dir)
    
    i = 1
    for font in fmh:
        with open(joinpath(out_dir, font_json_fmt.format(i, font['advance_width'], font['line_height'])), 'w') as f:
            json.dump(font, f, indent=4)
        i += 1
        
else:
    print ('Building AFT fontmap farc from directory "{}"'.format(inp_path))
    
    fmh = []
    
    # select and sort matching files by ascending font index
    files = [f for f in listdir(inp_path) if font_json_fmt_regex.match(f)]
    files.sort(key = lambda f: int(font_json_fmt_regex.match(f).group(1)))
    
    for fname in files:
        with open(joinpath(inp_path, fname), 'r') as f: 
            fmh += [json.load(f)]
    
    fmh_bytes = pyfmh3.to_bytes(fmh)
    farcdata = {'farc_type': 'FArC', 'files': {'fontmap.bin': {'data': fmh_bytes}}}
    
    if inp_path[-1] in ['/', '\\']:
        inp_path = inp_path[:-1]
    
    with open(inp_path + '.farc', 'wb') as f:
        pyfarc.to_stream(farcdata, f)