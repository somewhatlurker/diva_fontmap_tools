"""
pyfmh3 reader and writer for Project DIVA FMH3 fontmaps
can read+write AFT FMH3 and read X FONM
"""

from copy import deepcopy
from io import BytesIO
from pydiva.pyfmh3_formats import _eofc_struct, _fmh3_types


class UnsupportedFmh3TypeException(Exception):
    pass

def check_fmh3_type(t):
    """Checks if a fontmap type is supported and returns a remarks string. Raises UnsupportedFmh3TypeException if not supported."""
    
    if not t in _fmh3_types:
        raise UnsupportedFmh3TypeException("{} type not supported".format(t))
    
    return _fmh3_types[t]['remarks']


_fonts_pointers_min_offset = 32
_fonts_header_size_per_font = 32 # could be 28, but alignment is nicer with 32
_char_data_size = 8

def _fonts_header_pointers_size(n, address_size):
    """Returns the size of the pointers to font headers for the given number of fonts."""
    
    res = n * address_size
    if res % 16: res += 16 - (res % 16) # align to 16 bytes
    return res

def _fonts_header_size(n):
    """Returns the size of the fonts header section for the given number of fonts."""
    
    return n * _fonts_header_size_per_font

def _char_array_size(n):
    """Returns the size of a character info array for n characters."""
    
    res = n * _char_data_size
    if res % 16: res += 16 - (res % 16) # align to 16 bytes
    return res

def _set_font_pointers(fonts, address_size):
    """Sets font header pointers in the given list of fonts"""
    
    pos = _fonts_pointers_min_offset + _fonts_header_pointers_size(len(fonts), address_size)
    
    for font in fonts:
        font['pointer'] = pos
        pos += _fonts_header_size_per_font

def _set_char_pointers(fonts, address_size):
    """Sets character info pointers in the given list of fonts"""
    
    pos = _fonts_pointers_min_offset + _fonts_header_pointers_size(len(fonts), address_size) + _fonts_header_size(len(fonts))
    
    for font in fonts:
        font['data']['chars_pointer'] = pos
        pos += _char_array_size(len(font['data']['chars']))

def _get_fmh3_length(fonts):
    """Gets the full length of the FMH3 data from a font with pointers and char counts already set"""
    
    return fonts[-1]['data']['chars_pointer'] + _char_array_size(fonts[-1]['data']['chars_count'])


def to_stream(data, stream, no_copy=False):
    """
    Converts a dictionary (formatted like the dictionary returned by from_stream) to fontmap data and writes it to a stream.
    
    Set no_copy to True for a speedup and memory usage reduction if you don't mind your input data being contaminated.
    """
    
    magic_str = data['fmh3_type']
    check_fmh3_type(magic_str)
    fmh3_type = _fmh3_types[magic_str]
    
    if no_copy:
        fonts = data['fonts']
    if not no_copy:
        fonts = deepcopy(data['fonts'])
    
    for font in fonts:
        font['chars_count'] = len(font['chars'])
    fonts = [{'data': font} for font in fonts]
    
    address_size = fmh3_type['address_size']
    _set_font_pointers(fonts, address_size)
    _set_char_pointers(fonts, address_size)
    
    if fmh3_type['nest_fmh3_data']:
        data_size =_get_fmh3_length(fonts)
        return fmh3_type['struct'].build_stream(dict(
            data_size=data_size + _eofc_struct.sizeof(),
            data_pointer=64,
            fmh3_size=data_size,
            fmh3_data=dict(
                fonts_count=len(fonts),
                fonts_pointers_offset=_fonts_pointers_min_offset,
                fonts=fonts
            )
        ), stream)
    else:
        return fmh3_type['struct'].build_stream(dict(
            fonts_count=len(fonts),
            fonts_pointers_offset=_fonts_pointers_min_offset,
            fonts=fonts
        ), stream)

def to_bytes(data, no_copy=False):
    """
    Converts a dictionary (formatted like the dictionary returned by from_bytes) to an in-memory bytes object containing fontmap data.
    
    Set no_copy to True for a speedup and memory usage reduction if you don't mind your input data being contaminated.
    """
    
    with BytesIO() as s:
        to_stream(data, s, no_copy)
        return s.getvalue()


def _parsed_to_dict(fmhdata, nested_fmh):
    """Converts the raw construct data to our standard dictionary format."""
    
    magic_str = fmhdata['signature'].decode('ascii')
    if nested_fmh:
        fmhdata = fmhdata['fmh3_data']
    
    fonts = []
    
    for font in fmhdata['fonts']:
        tmp = dict(font['data'])
        del tmp['_io']
        del tmp['chars_count']
        del tmp['chars_pointer']
        tmp['chars'] = [dict(char) for char in tmp['chars']]
        for char in tmp['chars']:
            del char['_io']
        fonts += [tmp]
    
    return {'fmh3_type': magic_str, 'fonts': fonts}

def from_stream(s):
    """Converts fontmap data from a stream to a dictionary."""
    
    pos = s.tell()
    magic_str = s.read(4).decode('ascii')
    s.seek(pos)
    
    check_fmh3_type(magic_str)
    fmh3_type = _fmh3_types[magic_str]
    
    fmhdata = fmh3_type['struct'].parse_stream(s)
    return _parsed_to_dict(fmhdata, fmh3_type['nest_fmh3_data'])

def from_bytes(b):
    """Converts fontmap data from bytes to a dictionary."""
    
    with BytesIO(b) as s:
        return from_stream(s)


# test_fmh = {'fmh3_type': 'FMH3', 'fonts': [{"id":2, "advance_width":24, "line_height":30, "box_width":26, "box_height":32, "layout_param_1":3, "layout_param_2_numerator":1, "layout_param_2_denominator":1, "other_params?":0, "tex_size_chars":19, "chars":[{"codepoint":48, "halfwidth":False, "tex_col":0, "tex_row":0, "glyph_x":0, "glyph_width":24}, {"codepoint":49, "halfwidth":False, "tex_col":1, "tex_row":0, "glyph_x":0, "glyph_width":24}]}]}