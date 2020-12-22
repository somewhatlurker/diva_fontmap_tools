"""
FMH3 format information for pyfmh3
"""

from construct import Struct, Tell, Const, Padding, Int32ul, RepeatUntil, CString, Pointer, Byte, Int16ul, Flag, Int64ul, Bytes, Seek, If

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

_pof1_struct = Struct(
    "pointer_offset" / Tell,
    "signature" / Const(b'POF1'),
    "section_size" / Int32ul,
    "data_pointer" / Const(32, Int32ul),
    "flags" / Const(b'\x00\x00\x00\x10'),
    "depth" / Const(0, Int32ul),
    "data_size" / Int32ul,
    Padding(8),
    # hardcoded offset for this instead of pointer
    "data" / Bytes(lambda this: this.data_size)
)

_eofc_struct = Struct(
    "pointer_offset" / Tell,
    "signature" / Const(b'EOFC'),
    "section_size" / Const(0, Int32ul),
    "data_pointer" / Const(32, Int32ul),
    "flags" / Const(b'\x00\x00\x00\x10'),
    "depth" / Const(0, Int32ul),
    "data_size" / Const(0, Int32ul),
    Padding(8)
)

_fonm_format = Struct(
    "pointer_offset" / Tell,
    "signature" / Const(b'FONM'),
    "section_size" / Int32ul,
    "data_pointer" / Int32ul,
    "flags" / Const(b'\x00\x00\x00\x10'),
    "depth" / Const(0, Int32ul),
    "data_size" / Int32ul,
    "data" / Pointer(lambda this: this.data_pointer + this.pointer_offset, _fmh3_int64_format),
    # Seek(lambda this: this.data_pointer + this.data_size),
    # ENRS (endian reversal) ignored
    "extra_sections" / If(lambda this: this._building, Struct(
        "pof1" / Pointer(lambda this: this._.data_pointer + this._.data_size + this._.pointer_offset, _pof1_struct),
        Pointer(lambda this: this._.data_pointer + this._.data_size + this._.pointer_offset + this.pof1_size, _eofc_struct),
        Pointer(lambda this: this._.data_pointer + this._.section_size + this._.pointer_offset, _eofc_struct)
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