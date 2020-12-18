"""
Farc format information for pyfarc
"""

from construct import Struct, Const, Int32ub, Int32sb, RepeatUntil, CString, Pointer, Bytes, Padding, BitStruct, Flag, If, Seek, Tell

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


_FArc_format = Struct(
    "signature" / Const(b'FArc'),
    "header_size" / Int32ub, # doesn't include signature or header_size
    "alignment" / Int32sb,
    "files" / RepeatUntil(lambda obj,lst,ctx: ctx._io.tell() - 7 > ctx.header_size, Struct(
        "name" / CString("utf8"),
        "pointer" / Int32ub,
        "size" / Int32ub,
        "data" / Pointer(lambda this: this.pointer, Bytes(lambda this: this.size))
    )),
    #Padding(lambda this: this.alignment - (this._io.tell() % this.alignment) if this._io.tell() % this.alignment else 0)
)

_FArC_format = Struct(
    "signature" / Const(b'FArC'),
    "header_size" / Int32ub, # doesn't include signature or header_size
    "alignment" / Int32sb,
    "files" / RepeatUntil(lambda obj,lst,ctx: ctx._io.tell() - 7 > ctx.header_size, Struct(
        "name" / CString("utf8"),
        "pointer" / Int32ub,
        "compressed_size" / Int32ub,
        "uncompressed_size" / Int32ub,
        "data" / Pointer(lambda this: this.pointer, Bytes(lambda this: this.compressed_size))
    )),
    #Padding(lambda this: this.alignment - (this._io.tell() % this.alignment) if this._io.tell() % this.alignment else 0)
)

_FARC_format = Struct(
    "signature" / Const(b'FARC'),
    "header_size" / Int32ub, # doesn't include signature or header_size
    "flags" / BitStruct(
        Padding(29),
        "encrypted" / Flag,
        "compressed" / Flag,
        Padding(1)
    ),
    Padding(4),                     # if not encrypted or else popcnt of alignment is 1, use format field
    "alignment" / Int32sb,          # (if is encrypted and popcnt of alignment is not 1, assume FT format)
    "format" / Const(0, Int32sb),   # this struct only supports DT
    Padding(4),
    "files" / RepeatUntil(lambda obj,lst,ctx: ctx._io.tell() - 7 > ctx.header_size, Struct(
        "name" / CString("utf8"),
        "pointer" / Int32ub,
        "compressed_size" / Int32ub,
        "uncompressed_size" / Int32ub,
        "data" / Pointer(lambda this: this.pointer, Bytes(lambda this: (this.compressed_size + 16 - (this.compressed_size % 16)) if (this.compressed_size % 16 and this._.flags.encrypted) else (this.compressed_size)))
    )),
    #Padding(lambda this: this.alignment - (this._io.tell() % this.alignment) if this._io.tell() % this.alignment else 0)
)

_FARC_FT_format = Struct(
    "signature" / Const(b'FARC'),
    "header_size" / Int32ub, # doesn't include signature or header_size
    "flags" / BitStruct(
        Padding(29),
        "encrypted" / Flag,
        "compressed" / Flag,
        Padding(1)
    ),
    Padding(4),                     # if not encrypted or else popcnt of alignment is 1, use format field
    "alignment" / Int32sb,          # (if is encrypted and popcnt of alignment is not 1, assume FT format)
    "format" / Const(1, Int32sb),   # this struct only supports FT with unencrypted header
    "entry_count" / Int32sb,
    Padding(4),
    "files" / RepeatUntil(lambda obj,lst,ctx: (ctx._io.tell() - 7 > ctx.header_size) or (len(lst) >= ctx.entry_count), Struct(
        "name" / CString("utf8"),
        "pointer" / Int32ub,
        "compressed_size" / Int32ub,
        "uncompressed_size" / Int32ub,
        "flags" / BitStruct(
            Padding(29),
            "encrypted" / Flag,
            "compressed" / Flag,
            Padding(1)
        ),
        "file_end" / If(lambda this: this._parsing, Seek(lambda this: this._io.seek(0, 2))), # need to fix this up for write support
        "data" / Pointer(lambda this: this.pointer, Bytes(lambda this: min(this.file_end - this.pointer, (this.compressed_size + 16 - (this.compressed_size % 16)) if (this.compressed_size % 16 and this.flags.encrypted) else (this.compressed_size))))
    )),
    #Padding(lambda this: this.alignment - (this._io.tell() % this.alignment) if this._io.tell() % this.alignment else 0)
)

_farc_types = {
    'FArc': {
        'remarks': 'basic farc format',
        'struct': _FArc_format,
        'compression_support': False,
        'compression_forced': False,
        'fixed_header_size': 4,
        'files_header_fields_size': 8,
        'has_flags': False,
        'has_per_file_flags': False,
        'encryption_type': None,
        'write_support': True,
    },
    'FArC': {
        'remarks': 'farc with compression support',
        'struct': _FArC_format,
        'compression_support': True,
        'compression_forced': True,
        'fixed_header_size': 4,
        'files_header_fields_size': 12,
        'has_flags': False,
        'has_per_file_flags': False,
        'encryption_type': None,
        'write_support': True,
    },
    'FARC': {
        'remarks': 'farc with encryption and compression support (DT/F/X)',
        'struct': _FARC_format,
        'compression_support': True,
        'compression_forced': False,
        'fixed_header_size': 20,
        'files_header_fields_size': 12,
        'has_flags': True,
        'has_per_file_flags': False,
        'encryption_type': 'DT',
        'write_support': True,
    },
    'FARC_FT': {
        'remarks': 'farc with encryption and compression support (FT)',
        'struct': _FARC_FT_format,
        'compression_support': True,
        'compression_forced': False,
        'fixed_header_size': 24,
        'files_header_fields_size': 16,
        'has_flags': True,
        'has_per_file_flags': True,
        'encryption_type': 'FT',
        'write_support': False,
    },
}