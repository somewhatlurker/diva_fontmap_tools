"""
FT file helper functions for pyfarc
"""

from io import BytesIO
from secrets import token_bytes

try:
    from Crypto.Cipher import AES
except Exception:
    pass # main pyfarc module already handles this

def _needs_FT_decryption(s):
    """Checks if the FARC file stream needs FT-type decryption"""
    
    og_pos = s.tell()
    
    s.seek(og_pos + 11)
    encrypted = True if s.read(1)[0] & 4 else False
    
    s.seek(og_pos + 16)
    alignment_bits_popcnt = sum([bin(x).count('1') for x in s.read(4)])
    
    s.seek(og_pos + 20)
    format = s.read(4)
    
    # heuristic-based detection similar to MML
    if encrypted and (alignment_bits_popcnt != 1 or format[:3] != b'\x00\x00\x00'):
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
    new_header_size = old_header_size - 16 # iv seems to count towards header size
    
    out.write(new_header_size.to_bytes(4, byteorder='big', signed=False))
    out.write(s.read(8)) # other plaintext header stuff
    
    cipher = AES.new(b'\x13\x72\xD5\x7B\x6E\x9E\x31\xEB\xA2\x39\xB8\x3C\x15\x57\xC6\xBB', AES.MODE_CBC, iv=s.read(16))
    out.write(cipher.decrypt(s.read(old_header_size - 16 - 8))) # 16 is for IV, 8 is for plaintext part of header
    
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
    if new_header_size % 16: new_header_size += 16 - (new_header_size % 16) # pad for AES
    new_header_size += 8 # add size of plaintext parts back
    
    outstream.write(new_header_size.to_bytes(4, byteorder='big', signed=False))
    outstream.write(instream.read(8)) # other plaintext header stuff
    
    header_data = instream.read(old_header_size - 8) # header_size is 8 bytes longer than encrypted portion
    while len(header_data) != new_header_size - 16 - 8: # 16 is for IV, 8 is for plaintext part of header
        header_data += b'\x00'
    
    iv = token_bytes(16)
    outstream.write(iv)
    cipher = AES.new(b'\x13\x72\xD5\x7B\x6E\x9E\x31\xEB\xA2\x39\xB8\x3C\x15\x57\xC6\xBB', AES.MODE_CBC, iv=iv)
    outstream.write(cipher.encrypt(header_data))
    
    # resync streams (read old_header_size but wrote new_header_size)
    instream.seek(instream.tell() + new_header_size - old_header_size)
    
    outstream.write(instream.read())
    
    return