from PIL import Image, ImageDraw, ImageFont
from math import ceil
from os.path import join as joinpath
import json
import argparse

try:
    from fontTools.ttLib import TTFont
except ModuleNotFoundError:
    print ('fontTools not installed, please reinstall pip requirements')
    exit(1)


def firstFontWithCharacter(font_info, char, print_missing=False):
    # this checks the font's cmap (obtained via fonttools) for presence of a character
    # because pillow has no way to do that
    for font in font_info:
        if ord(char) in font['ft_cmap']:
            return font
    
    if print_missing: print ('No font found for character {} (0x{:04x})'.format(char, ord(char)))
    return font_info[0]

def get_args():
    parser = argparse.ArgumentParser(description='DIVA Font Generator')
    parser.add_argument('-f', '--font', default=None, help='source font file')
    parser.add_argument('-o', '--output_name', default=None, help='name for output png and json files')
    parser.add_argument('-c', '--charlist', default=joinpath('misc', 'charlist.txt'), help='path to charlist file to use (default: {})'.format(joinpath('misc', 'charlist.txt')))
    parser.add_argument('-v', '--variation', default=None, help='name of font variation to use (optional)')
    parser.add_argument('-i', '--ttc_index', default=None, help='font index for ttc files')
    parser.add_argument('-s', '--size', default=24, help='font size to use (optional)')
    parser.add_argument('-m', '--metrics', default=None, help='use manual size metrics (comma separated advance, line height, width, height)')
    parser.add_argument('--shrink', default=None, help='shrink the amount of space each character takes in its box by X pixels')
    parser.add_argument('--force_baseline', default=None, help='force the baseline position as a multiplier of font size (from the top of character box)')

    parser.add_argument('--list_variations', action='store_true', help='list available variations of the source font and exit')

    return parser.parse_args()

args = get_args()


if not args.font:
    print ('No font specified')
    exit(1)

# variations can be prepared later, after checking for list_variations
fontpaths = args.font.split(',')
if args.ttc_index:
    ttc_indices = args.ttc_index.split(',')
else:
    ttc_indices = ['0' for i in range(0, len(fontpaths))]
if args.shrink:
    fontshrinks = args.shrink.split(',')
else:
    fontshrinks = ['0' for i in range(0, len(fontpaths))]

if len(fontpaths) != len(ttc_indices):
    print ('Different number of fonts and ttc indices')
    exit(1)

if len(fontpaths) != len(fontshrinks):
    print ('Different number of fonts and shrink amounts')
    exit(1)

font_info = []
for i in range(0, len(fontpaths)):
    font_info += [{'path': fontpaths[i], 'ttc_index': ttc_indices[i], 'shrink': fontshrinks[i]}]

for font in font_info:
    try:
        font['pil_font'] = ImageFont.truetype(font['path'], int(args.size) - 1 - int(font['shrink']), int(font['ttc_index']))
        font['ft_font'] = TTFont(font['path'], fontNumber=int(font['ttc_index']))
        font['ft_cmap'] = font['ft_font'].getBestCmap()
    except Exception as e:
        print ('Error loading font: {}'.format(str(e)))
        exit(1)

    print ('Loaded font {}'.format(font['pil_font'].getname()[0]))


if args.list_variations:
    for font in font_info:
        name = font['pil_font'].getname()[0]
        try:
            vars = font['pil_font'].get_variation_names()
        except OSError:
            print ('{} has no variations'.format(name))
            continue
        
        print ('Variations of {}:'.format(name))
        for v in vars:
            print (' {}'.format(v))
    exit(0)

if args.variation:
    variations = args.variation.split(',')
    
    if len(font_info) != len(variations):
        print ('Different number of fonts and variations')
        exit(1)
    
    for i in range(0, len(font_info)):
        font_info[i]['variation'] = variations[i].strip()
    
    for font in font_info:
        if not font['variation']:
            continue
        
        try:
            font['pil_font'].set_variation_by_name(font['variation'])
        except Exception as e:
            print ('Error setting font variation: {}'.format(str(e)))
            exit(1)
    
        print ('Using variation {} for font {}'.format(font['variation'], font['pil_font'].getname()))


if not args.charlist:
    print ('No charlist specified')
    exit(1)

charlist = ''
try:
    with open(args.charlist, 'r', encoding='utf-16') as f:
        for char in f.read():
            if ord(char) <= 65535:
                charlist += char
            else:
                print ('Ignoring invalid character in charlist: {} (0x{:04x})'.format(char, ord(char)))
                print ('Only characters in the BMP (codepoint <= 65535) are supported')

except Exception as e:
    print ('Error loading charlist: {}'.format(str(e)))
    exit(1)

print ('Charlist: {}'.format(args.charlist))


if not args.output_name:
    print ('Output name not specified')
    exit(1)

print ('Outputting to {}'.format(args.output_name))


font_advance_size = (0, 0)
font_box_size = (0, 0)

# deliberately just use first font for main ascent and baseline values
font_ascent, font_baseline = font_info[0]['pil_font'].getmetrics() # tuple of the font ascent (the distance from the baseline to the highest outline point) and descent (the distance from the baseline to the lowest outline point, a negative value)
#font_baseline *= -1
full_ascent = font_ascent     # these are needed to ensure letters don't overlap
full_baseline = font_baseline # but fully using them breaks layout a bit
                              # we can use these as spacing, but position characters using the original ascender height

if args.metrics:
    m = args.metrics.split(',')
    if len(m) != 4:
        print ('Invalid number of custom metrics (must be 4)')
        exit(1)
    try:
        font_advance_size = (int(m[0]), int(m[1]))
        font_box_size = (int(m[2]), int(m[3]))
    except Exception as e:
        print ('Error parsing custom metrics: {}'.format(str(e)))
        exit(1)
else:
    max_char_width = 0
    for char in charlist: # iterate to find widest used char
        font = firstFontWithCharacter(font_info, char)
        junk, char_ascent, char_right, char_baseline = font['pil_font'].getbbox(char, anchor='ls')
        max_char_width = max(max_char_width, char_right)
        full_ascent = max(full_ascent, char_ascent * -1)
        full_baseline = max(full_baseline, char_baseline)
        

    font_box_size = (max_char_width + 1, full_ascent + full_baseline + 1) # height already is known from metrics
    
    # kanji_box_size can just use the first specified font
    # kanji_box_size/font_advance_size will be based on the actual space used by a full-size character
    kanji_box_size = max(font_info[0]['pil_font'].getbbox('鬱', anchor='lt')[2:]) + 1 # just using a square for now
    kanji_box_size = max(kanji_box_size, int(args.size)) # ensure advance and line height are at least equal to font size
    font_advance_size = (kanji_box_size, kanji_box_size)


# find the texture size to use and how many chars will fit in a row
def fits_in_tex(texture_size, char_size, num_chars):
    chars_per_row = texture_size[0] // char_size[0]
    if chars_per_row == 0: return False
    needed_rows = ceil(num_chars / chars_per_row)
    return texture_size[1] >= needed_rows * char_size[1]

texture_size = (1, 1)
while not fits_in_tex(texture_size, font_box_size, len(charlist)):
    if texture_size[0] > texture_size[1]:
        texture_size = (texture_size[0], texture_size[1] * 2)
    else:
        texture_size = (texture_size[0] * 2, texture_size[1])

chars_per_row = texture_size[0] // font_box_size[0]


max_halfwidth_width = ceil(font_box_size[0] / 2)


# get ready to draw
pil_image = Image.new('RGBA', (texture_size[0], texture_size[1]), color=0x00000000)
pil_draw = ImageDraw.Draw(pil_image)

coord = (0, font_ascent)
tex_idx = (0, 0)

if args.force_baseline != None:
    coord = (0, font_ascent * float(args.force_baseline))

out_chars = []
for char in charlist:
    font = firstFontWithCharacter(font_info, char, print_missing=True)
    width = font['pil_font'].getsize(char)[0]
    halfwidth = width <= max_halfwidth_width
    if halfwidth:
        x_adj = (max_halfwidth_width - width) // 2
    else:
        x_adj = (font_box_size[0] - width) // 2
    pil_draw.text((coord[0] + x_adj, coord[1]), char, fill=0xffffffff, font=font['pil_font'], anchor='ls')
    
    out_chars += [{
        "codepoint": ord(char),
        "halfwidth": halfwidth,
        "tex_col": tex_idx[0],
        "tex_row": tex_idx[1],
        "glyph_x": x_adj,
        "glyph_width": width
    }]
    
    tex_idx = (tex_idx[0] + 1, tex_idx[1])
    coord = (coord[0] + font_box_size[0], coord[1])
    if tex_idx[0] >= chars_per_row:
        tex_idx = (0, tex_idx[1] + 1)
        coord = (0, coord[1] + font_box_size[1])

pil_image.save('{}.png'.format(args.output_name), 'PNG')

out_font = {
    "id": 0,
    "advance_width": font_advance_size[0],
    "line_height": font_advance_size[1],
    "box_width": font_box_size[0],
    "box_height": font_box_size[1],
    "layout_param_1": 3,
    "layout_param_2_numerator": 1,
    "layout_param_2_denominator": 2,
    "other_params?": 0,
    "tex_size_chars": chars_per_row,
    "chars": out_chars
}

with open('{}.json'.format(args.output_name), 'w') as f:
    json.dump(out_font, f, indent=4)