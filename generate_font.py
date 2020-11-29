from PIL import Image, ImageDraw, ImageFont
from math import ceil
import json

charlist = ''
with open('AFT/fontmap/font9_24x24_charlist.txt', 'r', encoding='utf-16') as f:
    charlist = f.read()

font_name = 'dfpom3.ttc'
font_size = 23
font_advance_size = (0, 0)
font_box_size = (0, 0)


pil_font = ImageFont.truetype(font_name, font_size)

font_ascent, font_baseline = pil_font.getmetrics() # tuple of the font ascent (the distance from the baseline to the highest outline point) and descent (the distance from the baseline to the lowest outline point, a negative value)
#font_baseline *= -1
max_char_width = 0
for char in charlist:
    w = pil_font.getsize(char)[0] - pil_font.getoffset(char)[0]
    max_char_width = max(max_char_width, w)

font_box_size = (max_char_width, font_ascent + font_baseline)

kanji_box_size = max(pil_font.getbbox('鬱', anchor='lt')[2:]) + 1 # just using a square for now
font_advance_size = (kanji_box_size, kanji_box_size)



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

pil_image = Image.new('RGBA', (texture_size[0], texture_size[1]), color=0x00000000)
pil_draw = ImageDraw.Draw(pil_image)

coord = (0, font_ascent)
tex_idx = (0, 0)

out_chars = []
for char in charlist:
    offset = pil_font.getoffset(char)[0]
    # if offset: print (offset)
    width = pil_font.getsize(char)[0] - offset
    halfwidth = width <= font_box_size[0] // 2
    if halfwidth:
        x_adj = (font_box_size[0] // 2 - width) // 2
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

pil_image.save('gen_test.png', 'PNG')

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

with open('gen_test.json', 'w') as f:
    json.dump(out_font, f, indent=4)