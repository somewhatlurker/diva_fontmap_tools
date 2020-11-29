from PIL import Image, ImageDraw, ImageFont
from math import ceil
import json
import argparse

def get_args():
    parser = argparse.ArgumentParser(description='DIVA Font Generator')
    parser.add_argument('-f', '--font', default=None, help='source font file')
    parser.add_argument('-o', '--output_name', default=None, help='name for output png and json files')
    parser.add_argument('-c', '--charlist', default='charlist.txt', help='path to charlist file to use (default: charlist.txt)')
    parser.add_argument('-v', '--variation', default=None, help='name of font variation to use (optional)')
    parser.add_argument('-i', '--ttc_index', default=0, help='font index for ttc files')
    parser.add_argument('-s', '--size', default=24, help='font size to use (optional)')
    parser.add_argument('-m', '--metrics', default=None, help='use manual size metrics (comma separated advance, line height, width, height)')

    parser.add_argument('--list_variations', action='store_true', help='list available variations of the source font and exit')

    return parser.parse_args()

args = get_args()


if not args.font:
    print ('No font specified')
    exit(1)

try:
    pil_font = ImageFont.truetype(args.font, args.size - 1, args.ttc_index)
except Exception as e:
    print ('Error loading font: {}'.format(str(e)))
    exit(1)

print ('Loaded font {}'.format(pil_font.getname()[0]))


if args.list_variations:
    name = pil_font.getname()[0]
    try:
        vars = pil_font.get_variation_names()
    except OSError:
        print ('{} has no variations'.format(name))
        exit(1)
    
    print ('Variations of {}:'.format(name))
    for v in vars:
        print (' {}'.format(v))
    exit(0)

if args.variation:
    try:
        pil_font.set_variation_by_name(args.variation)
    except Exception as e:
        print ('Error setting font variation: {}'.format(str(e)))
        exit(1)
    
    print ('Using variation {}'.format(args.variation))


if not args.charlist:
    print ('No charlist specified')
    exit(1)

charlist = ''
try:
    with open(args.charlist, 'r', encoding='utf-16') as f:
        charlist = f.read()
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

font_ascent, font_baseline = pil_font.getmetrics() # tuple of the font ascent (the distance from the baseline to the highest outline point) and descent (the distance from the baseline to the lowest outline point, a negative value)
#font_baseline *= -1

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
        w = pil_font.getsize(char)[0] - pil_font.getoffset(char)[0]
        max_char_width = max(max_char_width, w)

    font_box_size = (max_char_width, font_ascent + font_baseline) # height already is known from metrics
    
    # kanji_box_size/font_advance_size will be based on the actual space used by a full-size character
    kanji_box_size = max(pil_font.getbbox('鬱', anchor='lt')[2:]) + 1 # just using a square for now
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


# get ready to draw
pil_image = Image.new('RGBA', (texture_size[0], texture_size[1]), color=0x00000000)
pil_draw = ImageDraw.Draw(pil_image)

coord = (0, font_ascent)
tex_idx = (0, 0)

out_chars = []
for char in charlist:
    offset = pil_font.getoffset(char)[0]
    # if offset: print (offset)
    width = pil_font.getsize(char)[0] - offset
    halfwidth = width <= ceil(font_box_size[0] / 2)
    if halfwidth:
        x_adj = (ceil(font_box_size[0] / 2) - width) // 2
    else:
        x_adj = (font_box_size[0] - width) // 2
    pil_draw.text((coord[0] + x_adj - offset, coord[1]), char, fill=0xffffffff, font=pil_font, anchor='ls')
    
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