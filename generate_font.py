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

try:
    from PIL import __version__ as _pil_version
    _pil_version = [int(v) for v in _pil_version.split('.')]
    if _pil_version[0] < 8:
        print ('Pillow version too low, please intall version 8+')
        exit(1)
except Exception:
    # I'd rather just continue than throw an error if this fails for some reason, like versioning changes
    # Users following instructions should never have a low version anyway
    pass

try:
    from fontTools import __version__ as _fonttools_version
    _fonttools_version = [int(v) for v in _fonttools_version.split('.')]
    if (_fonttools_version[0] < 3) or ((_fonttools_version[0] == 3) and (_fonttools_version[1] < 19)):
        print ('fontTools version too low, please intall version 3.19+')
        exit(1)
except Exception:
    # I'd rather just continue than throw an error if this fails for some reason, like versioning changes
    # Users following instructions should never have a low version anyway
    pass

try:
    from gooey import Gooey
    _gooey_installed = True
except Exception:
    _gooey_installed = False


def firstFontWithCharacter(font_info, char, print_missing=False):
    # this checks the font's cmap (obtained via fonttools) for presence of a character
    # because pillow has no way to do that
    for font in font_info:
        if ord(char) in font['ft_cmap']:
            return font
    
    if print_missing: print ('No font found for character {} (0x{:04x})'.format(char, ord(char)))
    return font_info[0]


def get_args(add_ignore_gooey=True):
    parser = argparse.ArgumentParser(description='DIVA Font Generator')
    output_args = parser.add_argument_group('Output', 'set the output options')
    output_args.add_argument('-o', '--output_name', default=None, help='name for output png and json files')
    output_args.add_argument('-c', '--charlist', default=joinpath('misc', 'charlist.txt'), help='path to charlist file to use (default: {})'.format(joinpath('misc', 'charlist.txt')))
    font_args = parser.add_argument_group('Per-Font Settings', 'set the fonts to use -- all arguments accept comma-separated lists for fallback font support')
    font_args.add_argument('-f', '--font', default=None, help='source font file(s)')
    font_args.add_argument('-v', '--variation', default=None, help='name of font variation(s) to use (optional)')
    font_args.add_argument('-i', '--ttc_index', default=None, help='font index for ttc files (optional, use 0 for ttf/otf)')
    font_args.add_argument('--shrink', default=None, help='shrink the amount of space each character takes in its box by X pixels (optional)')
    metrics_args = parser.add_argument_group('Font Metrics', 'set font size and positioning settings')
    metrics_args.add_argument('-s', '--size', default=24, help='font size to use (default: 24)')
    metrics_args.add_argument('-m', '--metrics', default=None, help='set to use manual size metrics (comma-separated advance, line height, width, height)')
    metrics_args.add_argument('--force_baseline', default=None, help='set to force the baseline position as a multiplier of font size (from the top of character box)')
    metrics_args.add_argument('--sega_style_proportional', action='store_true', help='use with fixed width fonts to add proportional-like rendering of halfwidth characters')
    special_args = parser.add_argument_group('Special Arguments', 'arguments that have special actions instead of affecting output')
    special_args.add_argument('--list_variations', action='store_true', help='list available variations of the source font(s) and exit')
    
    if add_ignore_gooey:
        parser.add_argument('--ignore-gooey', action='store_true', help=argparse.SUPPRESS)

    return parser.parse_args()

args = get_args()

if _gooey_installed and not args.output_name and not args.ignore_gooey:
    args = Gooey(get_args, use_cmd_args=True)(add_ignore_gooey=False)

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
        if not font['ft_cmap']: raise Exception('Couldn\'t find usable character map')
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
        char_left, char_ascent, char_right, char_baseline = font['pil_font'].getbbox(char, anchor='ls')
        if char_left > 0:
            char_left = 0 # match with calculation of width at render time
        max_char_width = max(max_char_width, char_right - char_left)
        full_ascent = max(full_ascent, char_ascent * -1)
        full_baseline = max(full_baseline, char_baseline)
        

    font_box_size = (max_char_width + 1, full_ascent + full_baseline + 2)
    
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
    
    # now use getbbox because it's more similar to the real positioning
    # and we can ensure we don't lose the left edge of characters
    bbox = font['pil_font'].getbbox(char, anchor='lt')
    
    # let characters get cut off by a pixel on the left in a vain attempt to maintain spacing,
    # but never more --- yeah, this is kinda useless ik
    # (bbox_adj becomes like bbox[0])
    if bbox[0] < 0:
        bbox_adj = bbox[0] + 1
    else:
        bbox_adj = 0
    
    width = bbox[2] - bbox_adj
    
    # add extra spacing so outline will definitely render well
    # if width + 2 <= font_box_size[0]:
    #     width += 2 # 2px extra width
    #     bbox_adj -= 1 # 1px shift right on rendering
    
    halfwidth = width <= max_halfwidth_width
    if halfwidth:
        x_adj = (max_halfwidth_width - width) // 2
    else:
        x_adj = (font_box_size[0] - width) // 2
    
    # subtract bbox_adj when drawing to properly position left edge with where we expect it
    # (draw_text internally adds an offset equal to bbox[:2])
    pil_draw.text((coord[0] + x_adj - bbox_adj, coord[1]), char, fill=0xffffffff, font=font['pil_font'], anchor='ls')
    
    if args.sega_style_proportional:
        # create an image to draw the character's mask into, then get that data
        # actual left coord: bbox[0] - bbox_adj
        # actual char width: bbox[2] - bbox[0]
        # needed width to render: actual width + actual left coord: bbox[2] - bbox_adj
        char_image = Image.new('L', (bbox[2] - bbox_adj, bbox[3] - bbox[1]), color=0x00000000)
        char_draw = ImageDraw.Draw(char_image)
        image_storage = font['pil_font'].getmask(char, mode='L', anchor='lt')
        # draw left edge at bbox[0] - bbox_adj to match draw_text's offset
        char_draw.draw.draw_bitmap((bbox[0] - bbox_adj, 0), image_storage, 255) # 255 is char_draw._getink(0xffffffff)[0], but removed to reduce undocumented internal calls
        char_data = char_image.getdata()
        
        # find the left and right pixel edges
        mark_x_first = -1
        mark_x_last = -1
        found_left_edge = False
        for x in range(0, char_image.width):
            col_has_pixels = False
            for y in range(0, char_image.height):
                p = char_data[x + y * char_image.width]
                if p:
                    col_has_pixels = True
                    break
            
            if col_has_pixels:
                mark_x_last = x
                if not found_left_edge:
                    mark_x_first = x
                    found_left_edge = True
        
        char_image.close()
        
        if mark_x_last >= 0: # only act upon characters with pixels in them
            mark_x_first = max(0, mark_x_first)
            mark_x_last = max(mark_x_first, mark_x_last)
            
            # add a little padding because it looks weird without it in AFT
            if mark_x_first > 0:
                mark_x_first -= 1
            
            # change the output values to write
            x_adj += mark_x_first
            width = mark_x_last - mark_x_first
            
            # add a little padding because it looks weird without it in AFT
            if x_adj + width < font_box_size[0]:
                width += 1
    
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