"""
pyfarc reader and writer for farc archives
"""

from copy import deepcopy
from io import BytesIO
import gzip
import zlib # gzip module's decompress doesn't handle junk at end of file
from pydiva.pyfarc_formats import _farc_types
from pydiva.pyfarc_ft_helpers import _is_FT_FARC, _decrypt_FT_farc

try:
    from Crypto.Cipher import AES
    _crypto_installed = True
except Exception:
    _crypto_installed = False


class UnsupportedFarcTypeException(Exception):
    pass

def check_farc_type(t):
    """Checks if a farc type is supported and returns a remarks string. Raises UnsupportedFarcTypeException if not supported."""
    
    if not t in _farc_types:
        raise UnsupportedFarcTypeException("{} type not supported".format(t))
    
    if _farc_types[t]['encryption_type'] and not _crypto_installed:
        raise UnsupportedFarcTypeException("{} type only supported with Crypto module installed".format(t))
    
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
    
    def _compress_files(files, farc_type):
        for fname, info in files.items():
            if info['flags']['compressed']:
                info['data_compressed'] = gzip.compress(info['data'], mtime=39) # set mtime for reproducible output
                if farc_type['compression_forced'] or (len(info['data_compressed']) < len(info['data'])):
                    info['flags']['compressed'] = True
                else:
                    info['data_compressed'] = info['data']
                    info['flags']['compressed'] = False
            else:
                info['data_compressed'] = info['data']
            
            info['len_compressed'] = len(info['data_compressed'])
    
    def _encrypt_files(files, farc_type):
        for fname, info in files.items():
            if not info['flags']['encrypted']:
                continue
            
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
    
    for fname, info in files.items():
        info['len_uncompressed'] = len(info['data'])
        
        if not 'flags' in info:
            info['flags'] = {}
        if not 'encrypted' in info['flags']:
            info['flags']['encrypted'] = flags.get('encrypted')
        if not 'compressed' in info['flags']:
            info['flags']['compressed'] = flags.get('compressed')
    
    if farc_type['compression_support']:
        _compress_files(files, farc_type)
    
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
    
    if not farc_type['write_support']:
        raise UnsupportedFarcTypeException('Writing {} type not supported'.format(magic_str))
    
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
                compressed_size=info['len_compressed'],
                uncompressed_size=info['len_uncompressed'],
                flags=info['flags'],
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
                size=info['len_uncompressed'],
                flags=info['flags'],
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
        flags = farcdata['flags']
        
        for f in farcdata['files']:
            data = f['data']
            
            if farc_type['has_per_file_flags']:
                flags = f['flags']
            
            if flags.get('encrypted'):
                if farc_type['encryption_type'] == 'DT':
                    cipher = AES.new(b'project_diva.bin', AES.MODE_ECB)
                    data = cipher.decrypt(data)
            
            if flags.get('compressed') and (farc_type['compression_forced'] or (f['uncompressed_size'] != f['compressed_size'])):
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
    
    if _is_FT_FARC(s):
        farc_type = _farc_types['FARC_FT']
        s = _decrypt_FT_farc(s)
    
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