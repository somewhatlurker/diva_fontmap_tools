"""
pyfmh3 reader and writer for Project DIVA FMH3 fontmaps
can read+write AFT FMH3 and read X FONM
"""

from construct import Struct, Tell, Const, Padding, Int32ul, RepeatUntil, CString, Pointer, Byte, Int16ul, Flag, Int64ul, Seek
from copy import deepcopy

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

_fonm_format = Struct(
    "signature" / Const(b'FONM'),
    "data_size" / Int32ul,
    "fmh3_pointer" / Int32ul,
    "unknown" / Int64ul,
    "fmh3_size" / Int32ul,
    "fmh3_data" / Pointer(lambda this: this.fmh3_pointer, _fmh3_int64_format),
    # Seek(lambda this: this.fmh3_pointer + this.fmh3_size),
    # "POF1" / Const( # no attempt made to parse and understand, though some parts would be trivial if needed
        # b'POF1' + b'\x20\x00\x00\x00' + b'\x20\x00\x00\x00' + b'\x00\x00\x00\x10'
        # + b'\x00\x00\x00\x00' + b'\x20\x00\x00\x00' + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00'
        # + b'\x19\x00\x00\x00' + b'BBAAAAAAAAADDDDDDDDDD' + b'\x00\x00\x00\x00' + b'\x00\x00\x00'
    # ),
    # "ENRS" / Const( # no attempt made to parse and understand, though some parts would be trivial if needed
        # b'ENRS' + b'\xB0\x00\x00\x00' + b'\x20\x00\x00\x00' + b'\x00\x00\x00\x10'
        # + b'\x00\x00\x00\x00' + b'\xB0\x00\x00\x00' + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00'
        # + b'\x00\x00\x00\x00' + b'\x15\x00\x00\x00' + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00' 
        # + b'\x04\x02\x18\x01' + b'\x10\x02\x14\x01' + b'\x1C\x01\x18\x01' + b'\x10\x01\x08\x01' 
        # + b'\x18\x01\x10\x01' + b'\x08\x01\x18\x01' + b'\x10\x01\x08\x01' + b'\x18\x01\x10\x01' 
        # + b'\x08\x01\x18\x01' + b'\x10\x01\x08\x01' + b'\x18\x01\x10\x01' + b'\x08\x01\x18\x01' 
        # + b'\x10\x01\x08\x01' + b'\x18\x01\x10\x01' + b'\x08\x01\x18\x01' + b'\x10\x01\x08\x01' 
        # + b'\x18\x01\x10\x01' + b'\x08\x02\x20\x0A' + b'\x10\x01\x1C\x03' + b'\x41\x40\x01\x08' 
        # + b'\x57\xEB\x00\x01' + b'\x80\x00\xBF\x60' + b'\x01\x08\x44\x4B' + b'\x00\x01\x62\x60' 
        # + b'\x01\x08\x41\x0D' + b'\x00\x01\x48\x70' + b'\x01\x08\x0D\x00' + b'\x01\x40\x70\x01' 
        # + b'\x08\x0D\x00\x01' + b'\x40\x70\x01\x08' + b'\x0D\x00\x01\x40' + b'\x70\x01\x08\x0D' 
        # + b'\x00\x01\x40\x70' + b'\x01\x08\x11\x00' + b'\x01\x40\x90\x01' + b'\x08\x56\xC1\x00' 
        # + b'\x01\x00\x00\x00' + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00'
    # ),
    # "EOFC1" / Const( # no attempt made to parse and understand, though some parts would be trivial if needed
        # b'EOFC' + b'\x00\x00\x00\x00' + b'\x20\x00\x00\x00' + b'\x00\x00\x00\x10'
        # + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00'
    # ),
    # "EOFC2" / Const( # no attempt made to parse and understand, though some parts would be trivial if needed
        # b'EOFC' + b'\x00\x00\x00\x00' + b'\x20\x00\x00\x00' + b'\x00\x00\x00\x10'
        # + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00'
    # ),
)

_fonts_pointers_min_offset = 32 # could be 16, but made larger in case X fontmap writing is added (plus this matches AFT fontmap anyway)
_fonts_pointers_size_per_font = 4 # this needs to be larger for writing X fontmaps
_fonts_header_size_per_font = 32 # could be 28, but alignment is nicer with 32
_char_data_size = 8

def _fonts_header_pointers_size(n):
    """Returns the size of the pointers to font headers for the given number of fonts."""
    
    res = n * _fonts_pointers_size_per_font
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

def _set_font_pointers(fonts):
    """Sets font header pointers in the given list of fonts"""
    
    pos = _fonts_pointers_min_offset + _fonts_header_pointers_size(len(fonts))
    
    for font in fonts:
        font['pointer'] = pos
        pos += _fonts_header_size_per_font

def _set_char_pointers(fonts):
    """Sets character info pointers in the given list of fonts"""
    
    pos = _fonts_pointers_min_offset + _fonts_header_pointers_size(len(fonts)) + _fonts_header_size(len(fonts))
    
    for font in fonts:
        font['data']['chars_pointer'] = pos
        pos += _char_array_size(len(font['data']['chars']))


def to_bytes(fonts, no_copy=False):
    """
    Converts a dictionary (formatted like the dictionary returned by from_bytes) to an in-memory bytes object containing fontmap data.
    
    Set no_copy to True for a speedup and memory usage reduction if you don't mind your input data being contaminated.
    """
    
    if not no_copy:
        fonts = deepcopy(fonts)
    
    for font in fonts:
        font['chars_count'] = len(font['chars'])
    fonts = [{'data': font} for font in fonts]
    _set_font_pointers(fonts)
    _set_char_pointers(fonts)
    
    return _fmh3_format.build(dict(
        fonts_count=len(fonts),
        fonts_pointers_offset=_fonts_pointers_min_offset,
        fonts=fonts
    ))

def to_stream(data, stream, no_copy=False):
    """
    Converts a dictionary (formatted like the dictionary returned by from_stream) to fontmap data and writes it to a stream.
    
    Set no_copy to True for a speedup and memory usage reduction if you don't mind your input data being contaminated.
    """
    
    if not no_copy:
        fonts = deepcopy(fonts)
    
    for font in fonts:
        font['chars_count'] = len(font['chars'])
    fonts = [{'data': font} for font in fonts]
    _set_font_pointers(fonts)
    _set_char_pointers(fonts)
    
    return _fmh3_format.build_stream(dict(
        fonts_count=len(fonts),
        fonts_pointers_offset=_fonts_pointers_min_offset,
        fonts=fonts
    ), stream)


def _parsed_to_dict(fmhdata):
    """Converts the raw construct data to our standard dictionary format."""
    
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

    return fonts

class UnsupportedFileException(Exception):
    pass

def from_bytes(b):
    """Converts fontmap data from bytes to a dictionary."""
    
    magic_str = b[:4].decode('ascii')
    
    if magic_str == 'FMH3':
        fmhdata = _fmh3_format.parse(b)
    elif magic_str == 'FONM':
        fmhdata = _fonm_format.parse(b)['fmh3_data']
    else:
        raise UnsupportedFileException("{} type not supported".format(magic_str))
    
    return _parsed_to_dict(fmhdata)

def from_stream(s):
    """Converts fontmap data from a stream to a dictionary."""
    
    pos = s.tell()
    magic_str = s.read(4).decode('ascii')
    s.seek(pos)
    
    if magic_str == 'FMH3':
        fmhdata = _fmh3_format.parse_stream(s)
    elif magic_str == 'FONM':
        fmhdata = _fonm_format.parse_stream(s)['fmh3_data']
    else:
        raise UnsupportedFileException("{} type not supported".format(magic_str))
    
    return _parsed_to_dict(fmhdata)