"""
pyfarc reader and writer for farc archives
supports Farc and FarC only
"""

from construct import Struct, Const, Int32ub, Int32sb, RepeatUntil, CString, Pointer, Bytes, Padding, BitStruct, Flag
from copy import deepcopy
from io import BytesIO
import gzip
import zlib # gzip module's decompress doesn't handle junk at end of file

try:
    from Crypto.Cipher import AES
    _crypto_installed = True
except Exception:
    _crypto_installed = False

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
    Padding(4),                     # if not encrypted or else popcnt of alignment is 1, assume DT format
    "alignment" / Int32sb,          # (if is encrypted and popcnt of alignment is not 1, assume FT format)
    "format" / Const(0, Int32sb),   # this struct only supports DT
    "entry_count" / Int32sb,
    "files" / RepeatUntil(lambda obj,lst,ctx: ctx._io.tell() - 7 > ctx.header_size, Struct(
        "name" / CString("utf8"),
        "pointer" / Int32ub,
        "compressed_size" / Int32ub,
        "uncompressed_size" / Int32ub,
        "data" / Pointer(lambda this: this.pointer, Bytes(lambda this: (this.compressed_size + 16 - (this.compressed_size % 16)) if (this.compressed_size % 16 and this._.flags.encrypted) else (this.compressed_size)))
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
        'encryption_type': None,
    },
    'FArC': {
        'remarks': 'farc with compression support',
        'struct': _FArC_format,
        'compression_support': True,
        'compression_forced': True,
        'fixed_header_size': 4,
        'files_header_fields_size': 12,
        'has_flags': False,
        'encryption_type': None,
    },
    'FARC': {
        'remarks': 'farc with encryption and compression support (DT)',
        'struct': _FARC_format,
        'compression_support': True,
        'compression_forced': False,
        'fixed_header_size': 20,
        'files_header_fields_size': 12,
        'has_flags': True,
        'encryption_type': 'DT',
    },
}

class UnsupportedFarcTypeException(Exception):
    pass

def check_farc_type(t):
    """Checks if a farc type is supported and returns a remarks string. Raises UnsupportedFarcTypeException if not supported."""
    
    if not t in _farc_types:
        raise UnsupportedFarcTypeException("{} type not supported".format(t))
    
    if _farc_types[t]['encryption_type'] and not _crypto_installed:
        raise UnsupportedFarcTypeException("{} type only supported with Crypto module installed (DT format only)".format(t))
    
    return _farc_types[t]['remarks']


def _files_header_size_calc(files, farc_type):
    """Sums the size of the files header section for the given files and farc_type data."""
    
    size = 0
    for fname, info in files.items():
        size += len(fname) + 1
        size += farc_type['files_header_fields_size']
    return size

def _prep_files(files, alignment, farc_type, flags):
    """Gets files ready for writing by compressing them and calculating pointers."""
    
    def _compress_files(files, farc_type, enable_compression):
        for fname, info in files.items():
            if enable_compression:
                info['data_compressed'] = gzip.compress(info['data'], mtime=39) # set mtime for reproducible output
                if farc_type['compression_forced'] or (len(info['data_compressed']) < len(info['data'])):
                    info['compressed'] = True
                else:
                    info['data_compressed'] = info['data']
                    info['compressed'] = False
            else:
                info['data_compressed'] = info['data']
                info['compressed'] = False
    
    def _encrypt_files(files, farc_type):
        for fname, info in files.items():
            if 'data_compressed' in info:
                data = info['data_compressed']
            else:
                data = info['data']
            
            while len(data) % 16:
                data += b'\x00'
            
            if farc_type['encryption_type'] == 'DT':
                cipher = AES.new(b'project_diva.bin', AES.MODE_ECB)
                data = cipher.encrypt(data)
            
            if 'data_compressed' in info:
                info['data_compressed'] = data
                if not info['compressed']:
                    # fix lengths to match so that decompression won't be attempted
                    while len(info['data']) < len(data):
                        info['data'] += b'\x00'
            else:
                info['data'] = data
       
    def _set_files_pointers(files, alignment, farc_type):
        pos = 8 + farc_type['fixed_header_size'] + _files_header_size_calc(files, farc_type)
        
        for fname, info in files.items():
            if pos % alignment: pos += alignment - (pos % alignment)
            info['pointer'] = pos
            if 'data_compressed' in info:
                pos += len(info['data_compressed'])
            else:
                pos += len(info['data'])
    
    if farc_type['compression_support']:
        _compress_files(files, farc_type, flags.get('compressed'))
    
    if flags.get('encrypted') and farc_type['encryption_type']:
        _encrypt_files(files, farc_type)
    
    _set_files_pointers(files, alignment, farc_type)


def to_stream(data, stream, alignment=1, no_copy=False):
    """
    Converts a farc dictionary (formatted like the dictionary returned by from_stream) to farc data and writes it to a stream.
    
    Set no_copy to True for a speedup and memory usage reduction if you don't mind your input data being contaminated.
    """
    
    magic_str = data['farc_type']
    check_farc_type(magic_str)
    farc_type = _farc_types[magic_str]
    
    flags = {'encrypted': False, 'compressed': farc_type['compression_forced']}
    if farc_type['has_flags'] and 'flags' in data:
        flags['compressed'] = data['flags'].get('compressed')
        flags['encrypted'] = data['flags'].get('encrypted')
        
    
    if no_copy:
        files = data['files']
    else:
        files = deepcopy(data['files'])
    _prep_files(files, alignment, farc_type, flags)
    
    if farc_type['compression_support']:
        return farc_type['struct'].build_stream(dict(
            header_size=farc_type['fixed_header_size'] + _files_header_size_calc(files, farc_type),
            flags=flags,
            entry_count=len(files),
            alignment=alignment,
            files=[dict(
                name=fname,
                pointer=info['pointer'],
                compressed_size=len(info['data_compressed']),
                uncompressed_size=len(info['data']),
                data=info['data_compressed']
            ) for fname, info in files.items()]
        ), stream)
    else:
        return farc_type['struct'].build_stream(dict(
            header_size=farc_type['fixed_header_size'] + _files_header_size_calc(files, farc_type),
            flags=flags,
            entry_count=len(files),
            alignment=alignment,
            files=[dict(
                name=fname,
                pointer=info['pointer'],
                size=len(info['data']),
                data=info['data']
            ) for fname, info in files.items()]
        ), stream)

def to_bytes(data, alignment=1, no_copy=False):
    """
    Converts a farc dictionary (formatted like the dictionary returned by from_bytes) to an in-memory bytes object containing farc data.
    
    Set no_copy to True for a speedup and memory usage reduction if you don't mind your input data being contaminated.
    """
    
    with BytesIO() as s:
        to_stream(data, s, alignment, no_copy)
        return s.getvalue()


def _parsed_to_dict(farcdata, farc_type):
    """Converts the raw construct data to our standard dictionary format."""
    
    files = {}
    
    if farc_type['has_flags']:
        for f in farcdata['files']:
            data = f['data']
            
            if farcdata['flags'].get('encrypted'):
                if farc_type['encryption_type'] == 'DT':
                    cipher = AES.new(b'project_diva.bin', AES.MODE_ECB)
                    data = cipher.decrypt(data)
            
            if farcdata['flags'].get('compressed') and (farc_type['compression_forced'] or (f['uncompressed_size'] != f['compressed_size'])):
                data = zlib.decompress(data, wbits=16+zlib.MAX_WBITS, bufsize=f['uncompressed_size'])
            
            files[f['name']] = {'data': data}
    
    elif farc_type['compression_support']:
        for f in farcdata['files']:
            data = f['data']
            
            if farc_type['compression_forced'] or (f['uncompressed_size'] != f['compressed_size']):
                data = zlib.decompress(data, wbits=16+zlib.MAX_WBITS, bufsize=f['uncompressed_size'])
            
            files[f['name']] = {'data': data}
    
    else:
        for f in farcdata['files']:
            data = f['data']
            files[f['name']] = {'data': data}
    
    out = {'farc_type': farcdata['signature'].decode('ascii'), 'files': files}
    if farc_type['has_flags']:
        out['flags'] = farcdata['flags']
    return out

def from_stream(s):
    """Converts farc data from a stream to a dictionary."""
    
    pos = s.tell()
    magic_str = s.read(4).decode('ascii')
    check_farc_type(magic_str)
    farc_type = _farc_types[magic_str]
    s.seek(pos)
    
    farcdata = farc_type['struct'].parse_stream(s)
    return _parsed_to_dict(farcdata, farc_type)

def from_bytes(b):
    """Converts farc data from bytes to a dictionary."""
    
    with BytesIO(b) as s:
        return from_stream(s)


#test_farc = {'farc_type': 'FArc', 'files': {'aaa': {'data': b'test1'}, 'bbb': {'data': b'test2'}, 'ccc': {'data': b'aaaaaaaaaaaaaaaaaaaaaaaa'}}}
#test_farc = {'farc_type': 'FArC', 'files': {'aaa': {'data': b'test1'}, 'bbb': {'data': b'test2'}, 'ccc': {'data': b'aaaaaaaaaaaaaaaaaaaaaaaa'}}}
#test_farc = {'farc_type': 'FARC', 'files': {'aaa': {'data': b'test1'}, 'bbb': {'data': b'test2'}, 'ccc': {'data': b'aaaaaaaaaaaaaaaaaaaaaaaa'}}}
#test_farc = {'farc_type': 'FARC', 'files': {'aaa': {'data': b'test1'}, 'bbb': {'data': b'test2'}, 'ccc': {'data': b'aaaaaaaaaaaaaaaaaaaaaaaa'}}, 'flags': {'encrypted': True}}
#test_farc = {'farc_type': 'FARC', 'files': {'aaa': {'data': b'test1'}, 'bbb': {'data': b'test2'}, 'ccc': {'data': b'aaaaaaaaaaaaaaaaaaaaaaaa'}}, 'flags': {'compressed': True}}
#test_farc = {'farc_type': 'FARC', 'files': {'aaa': {'data': b'test1'}, 'bbb': {'data': b'test2'}, 'ccc': {'data': b'aaaaaaaaaaaaaaaaaaaaaaaa'}}, 'flags': {'encrypted': True, 'compressed': True}}
#print (test_farc)

#test_bytes = to_bytes(test_farc, alignment=16)
#print (test_bytes)
#print (from_bytes(test_bytes))

#with open('test.farc', 'wb') as f:
#    to_stream(test_farc, f, alignment=16)
#with open('test.farc', 'rb') as f:
#    print (from_stream(f))

#with open('shader_amd.farc', 'rb') as f:
#    shaderfarc = from_stream(f)
#with open('shader_amd_out.farc', 'wb') as f:
#    to_stream(shaderfarc, f, alignment=16, no_copy=True)

#with open('shader_amd_compressed.farc', 'rb') as f:
#    shaderfarc = from_stream(f)
#with open('shader_amd_out_compressed.farc', 'wb') as f:
#    to_stream(shaderfarc, f, alignment=1, no_copy=True)

#with open('fontmap.farc', 'rb') as f:
#    fontmapfarc = from_stream(f)
#with open('fontmap_out.farc', 'wb') as f:
#    to_stream(fontmapfarc, f, alignment=1, no_copy=True)