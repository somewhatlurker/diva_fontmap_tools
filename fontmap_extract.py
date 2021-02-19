from os.path import dirname, exists as pathexists, isfile, splitext, join as joinpath, basename
from os import listdir, mkdir, remove as removefile
from sys import argv, exit
from re import compile as re_compile
import json

try:
    from pydiva import pyfmh3
    from pydiva import pyfarc
    from pydiva.farc_load_helper import farc_load_helper
except ModuleNotFoundError:
    print ('pydiva not installed, please reinstall pip requiremets')
    exit(1)


font_json_fmt = 'font{}_{}x{}.json'
font_json_fmt_regex = re_compile(r'font(\d+)(_\d+x\d+)?\.json$')

fontmap_farc_filenames = {
    'FMH3': 'fontmap.bin',
    'FONM': 'fontmap.fnm',
    'FONM_F2': 'fontmap.fnm',
}


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
        farc_files = farc_load_helper(f, fontmap_farc_filenames.values())
    
    if len(farc_files) == 0:
        print ('Error: Found farc with no known fontmap files')
        exit(1)
    elif farc_files[0][0]:
        print ('Loading {} from farc'.format(farc_files[0][0]))
    
    try:
        fmh = pyfmh3.from_bytes(farc_files[0][1])
    except Exception as e:
        print ('Error: {}'.format(e))
        exit(1)
    
    out_dir = inp_path
    while '.' in basename(out_dir):
        out_dir = splitext(out_dir)[0]
    
    if pathexists(out_dir):
        clean_dir(out_dir)
    else:
        mkdir(out_dir)
    
    i = 1
    for font in fmh['fonts']:
        with open(joinpath(out_dir, font_json_fmt.format(i, font['advance_width'], font['line_height'])), 'w') as f:
            json.dump(font, f, indent=4)
        i += 1
    
    del fmh['fonts']
    with open(joinpath(out_dir, 'meta.json'), 'w') as f:
        json.dump(fmh, f, indent=4)
        
else:
    print ('Building fontmap farc from directory "{}"'.format(inp_path))
    
    fonts = []
    
    # select and sort matching files by ascending font index
    files = [f for f in listdir(inp_path) if font_json_fmt_regex.match(f)]
    files.sort(key = lambda f: int(font_json_fmt_regex.match(f).group(1)))
    
    for fname in files:
        with open(joinpath(inp_path, fname), 'r') as f: 
            fonts += [json.load(f)]
    
    try:
        with open(joinpath(inp_path, 'meta.json'), 'r') as f:
            fmh = json.load(f)
    except:
        fmh = {'fmh3_type': 'FMH3'}
    
    fmh['fonts'] = fonts
    
    fmh_bytes = pyfmh3.to_bytes(fmh)
    farcdata = {'farc_type': 'FArC', 'files': {fontmap_farc_filenames[fmh['fmh3_type']]: {'data': fmh_bytes}}}
    
    if inp_path[-1] in ['/', '\\']:
        inp_path = inp_path[:-1]
    
    with open(inp_path + '.farc', 'wb') as f:
        pyfarc.to_stream(farcdata, f)