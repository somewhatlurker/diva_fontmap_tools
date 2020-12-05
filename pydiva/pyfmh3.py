"""
pyfmh3 reader and writer for Project DIVA FMH3 fontmaps
can read+write AFT FMH3 and read X FONM
"""

from construct import Struct, Tell, Const, Padding, Int32ul, RepeatUntil, CString, Pointer, Byte, Int16ul, Flag, Int64ul, Seek, If
from copy import deepcopy
from io import BytesIO

_construct_version = None
try:
    from construct import __version__ as _construct_version
    _construct_version = [int(v) for v in _construct_version.split('.')]
except Exception:
    # I'd rather just continue than throw an error if this fails for some reason, like versioning changes,
    # so just let _construct_version be None
    # Users following instructions should never have a low version anyway
    pass

if _construct_version:
    if (_construct_version[0] < 2) or ((_construct_version[0] == 2) and (_construct_version[1] < 9)):
        raise Exception('Construct version too low, please install version 2.9+')


_fmh3_format = Struct(
    "pointer_offset" / Tell,
    "signature" / Const(b'FMH3'),
    Padding(4),
    "fonts_count" / Int32ul,
    "fonts_pointers_offset" / Int32ul,
    "fonts" / Pointer(lambda this: this.fonts_pointers_offset + this.pointer_offset, RepeatUntil(lambda obj,lst,ctx: ctx._index >= ctx.fonts_count - 1, Struct(
        "pointer" / Int32ul,
        "data" / Pointer(lambda this: this.pointer + this._.pointer_offset, Struct(
            "id" / Int32ul,
            "advance_width" / Byte,
            "line_height" / Byte,
            "box_width" / Byte,
            "box_height" / Byte,
            "layout_param_1" / Byte, 
            "layout_param_2_numerator" / Byte,
            "layout_param_2_denominator" / Byte,
            Padding(1),
            "other_params?" / Int32ul,
            "tex_size_chars" / Int32ul,
            "chars_count" / Int32ul,
            "chars_pointer" / Int32ul,
            "chars" / Pointer(lambda this: this.chars_pointer + this._._.pointer_offset, RepeatUntil(lambda obj,lst,ctx: ctx._index >= ctx.chars_count - 1, Struct(
                "codepoint" / Int16ul,
                "halfwidth" / Flag,
                Padding(1),
                "tex_col" / Byte,
                "tex_row" / Byte,
                "glyph_x" / Byte,
                "glyph_width" / Byte,
            ))),
        )),
    ))),
)

_fmh3_int64_format = Struct(
    "pointer_offset" / Tell,
    "signature" / Const(b'FMH3'),
    Padding(4),
    "fonts_count" / Int64ul,
    "fonts_pointers_offset" / Int64ul,
    "fonts" / Pointer(lambda this: this.fonts_pointers_offset + this.pointer_offset, RepeatUntil(lambda obj,lst,ctx: ctx._index >= ctx.fonts_count - 1, Struct(
        "pointer" / Int64ul,
        "data" / Pointer(lambda this: this.pointer + this._.pointer_offset, Struct(
            "id" / Int32ul,
            "advance_width" / Byte,
            "line_height" / Byte,
            "box_width" / Byte,
            "box_height" / Byte,
            "layout_param_1" / Byte, 
            "layout_param_2_numerator" / Byte,
            "layout_param_2_denominator" / Byte,
            Padding(1),
            "other_params?" / Int32ul,
            "tex_size_chars" / Int32ul,
            "chars_count" / Int32ul,
            "chars_pointer" / Int32ul,
            "chars" / Pointer(lambda this: this.chars_pointer + this._._.pointer_offset, RepeatUntil(lambda obj,lst,ctx: ctx._index >= ctx.chars_count - 1, Struct(
                "codepoint" / Int16ul,
                "halfwidth" / Flag,
                Padding(1),
                "tex_col" / Byte,
                "tex_row" / Byte,
                "glyph_x" / Byte,
                "glyph_width" / Byte,
            ))),
        )),
    ))),
)

_eofc_struct = Struct(
    "pointer_offset" / Tell,
    "signature" / Const(b'EOFC'),
    "data_size" / Const(0, Int32ul),
    "data_pointer" / Const(32, Int32ul),
    "flags" / Const(b'\x00\x00\x00\x10'),
    "depth" / Const(0, Int32ul),
    Padding(12)
)

_fonm_format = Struct(
    "pointer_offset" / Tell,
    "signature" / Const(b'FONM'),
    "data_size" / Int32ul,
    "data_pointer" / Int32ul,
    "flags" / Const(b'\x00\x00\x00\x10'),
    "depth" / Const(0, Int32ul),
    "fmh3_size" / Int32ul,
    "fmh3_data" / Pointer(lambda this: this.data_pointer + this.pointer_offset, _fmh3_int64_format),
    # Seek(lambda this: this.data_pointer + this.fmh3_size),
    # POF1 (relocation) ignored
    # ENRS (endian reversal) ignored
    If(lambda this: this._building, Struct(
        Pointer(lambda this: this._.data_pointer + this._.fmh3_size + this._.pointer_offset, _eofc_struct),
        Pointer(lambda this: this._.data_pointer + this._.data_size + this._.pointer_offset, _eofc_struct)
    )),
)

_fmh3_types = {
    'FMH3': {
        'remarks': 'unencapsulated FT fontmap',
        'struct': _fmh3_format,
        'address_size': 4,
        'nest_fmh3_data': False,
    },
    'FONM': {
        'remarks': 'X fontmap in FONM container',
        'struct': _fonm_format,
        'address_size': 8,
        'nest_fmh3_data': True,
    },
}

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