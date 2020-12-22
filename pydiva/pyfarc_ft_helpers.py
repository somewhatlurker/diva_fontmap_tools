"""
FT file helper functions for pyfarc
"""

from io import BytesIO
from secrets import token_bytes
from os import getenv

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
except Exception:
    pass # main pyfarc module already handles this

def _needs_FT_decryption(s):
    """Checks if the FARC file stream needs FT-type decryption"""
    
    og_pos = s.tell()
    
    s.seek(og_pos + 11)
    encrypted = True if s.read(1)[0] & 4 else False
    
    s.seek(og_pos + 16)
    alignment = s.read(4)
    alignment_bits_popcnt = sum([bin(x).count('1') for x in alignment])
    
    s.seek(og_pos + 20)
    format = s.read(4)
    
    # heuristic-based detection similar to MML -- this should have a false negative rate of ~1 in 4.8b (compared to MML's ~1 in 134.2m)
    # false positives will require either more than 8 bits set in popcnt (extremely unlikely) or a new subformat which would be unsupported anyway
    # if many bits (>8) are set in alignment, it seems incorrect -- likely encrypted (~1 in 285 false negative)
    # if format doesn't start with null bytes, it seems incorrect -- likely encrypted (~1 in 16.8m false negative)
    # if the entire 16 bytes are null, it indicates a null IV and definite encryption (or a bad file)
    s.seek(og_pos + 16) # prepare for reading entire IV
    if encrypted and (alignment_bits_popcnt > 8 or format[:3] != b'\x00\x00\x00' or s.read(16) == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'):
        s.seek(og_pos)
        return True
    
    s.seek(og_pos)
    return False

def _is_FT_FARC(s):
    """Returns whether the FARC file stream is in FT format"""
    
    og_pos = s.tell()
    magic_str = s.read(4).decode('ascii')
    s.seek(og_pos)
    
    if magic_str != 'FARC':
        return False
        
    if _needs_FT_decryption(s):
        return True
    
    
    s.seek(og_pos + 20)
    format = s.read(4)
    s.seek(og_pos)
    
    if format == b'\x00\x00\x00\x01':
        return True
    
    return False

def _decrypt_FT_FARC_header(s):
    """
    Decrypts header of FT FARC from stream and returns a new stream containing entire farc
    """
    
    if not _is_FT_FARC(s):
        return None
    
    if not _needs_FT_decryption(s):
        return None
    
    og_pos = s.tell()
    
    out = BytesIO()
    
    out.write(s.read(4)) # signature
    
    old_header_size = int.from_bytes(s.read(4), byteorder='big', signed=False)
    other_plaintext_header = s.read(8) # other plaintext header stuff
    
    cipher = AES.new(b'\x13\x72\xD5\x7B\x6E\x9E\x31\xEB\xA2\x39\xB8\x3C\x15\x57\xC6\xBB', AES.MODE_CBC, iv=s.read(16))
    header_data = cipher.decrypt(s.read(old_header_size - 16 - 8)) # 16 is for IV, 8 is for plaintext part of header
    header_data = unpad(header_data, 16, 'pkcs7')
    new_header_size = len(header_data) + 8
    
    out.write(new_header_size.to_bytes(4, byteorder='big', signed=False))
    out.write(other_plaintext_header)
    out.write(header_data)
    
    # resync streams (read old_header_size but wrote new_header_size)
    out.seek(out.tell() + old_header_size - new_header_size)
    
    out.write(s.read())
    
    s.seek(og_pos)
    out.seek(0)
    return out

def _encrypt_FT_FARC_header(instream, outstream):
    """
    Encrypts header of FT FARC from instream and writes entire FARC to outstream
    Ensure input FARC has enough space for IV and AES padding after the header
    """
    
    if not _is_FT_FARC(instream) or _needs_FT_decryption(instream):
        # file doesn't need encryption???
        #outstream.write(instream.read())
        #return
        raise Exception('Wrong format FARC or already encrypted')
    
    outstream.write(instream.read(4)) # signature
    
    old_header_size = int.from_bytes(instream.read(4), byteorder='big', signed=False)
    new_header_size = old_header_size - 8 # temporarily remove stuff that isn't encrypted
    new_header_size += 16 # iv seems to count towards header size
    new_header_size += 16 - (new_header_size % 16) # space for AES padding
    new_header_size += 8 # add size of plaintext parts back
    
    outstream.write(new_header_size.to_bytes(4, byteorder='big', signed=False))
    outstream.write(instream.read(8)) # other plaintext header stuff
    
    header_data = instream.read(old_header_size - 8) # header_size is 8 bytes longer than encrypted portion
    header_data = pad(header_data, 16, 'pkcs7')
    
    if new_header_size != len(header_data) + 16 + 8: # 16 is for IV, 8 is for plaintext part of header
        raise Exception('Header size calc is bugged! Please report this! actual: {}, expected: {}'.format(len(header_data) + 16 + 8, new_header_size))
    
    if getenv('PYFARC_NULL_IV'):
        iv = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    else:
        iv = token_bytes(16)
    outstream.write(iv)
    cipher = AES.new(b'\x13\x72\xD5\x7B\x6E\x9E\x31\xEB\xA2\x39\xB8\x3C\x15\x57\xC6\xBB', AES.MODE_CBC, iv=iv)
    outstream.write(cipher.encrypt(header_data))
    
    # resync streams (read old_header_size but wrote new_header_size)
    instream.seek(instream.tell() + new_header_size - old_header_size)
    
    outstream.write(instream.read())
    
    return