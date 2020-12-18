"""
FT file helper functions for pyfarc
"""

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

def _decrypt_FT_farc(s):
    """Returns a decrypted copy of the FT FARC file stream"""
    
    if not _is_FT_FARC(s):
        return s
    
    if not _needs_FT_decryption(s):
        return s
    
    og_pos = s.tell()
    
    out = BytesIO()
    s.seek(0)
    out.write(s.read(16))
    cipher = AES.new(b'\x13\x72\xD5\x7B\x6E\x9E\x31\xEB\xA2\x39\xB8\x3C\x15\x57\xC6\xBB', AES.MODE_CBC, iv=s.read(16))
    data = cipher.decrypt(s.read())
    out.write(data)
    
    s.seek(og_pos)
    out.seek(og_pos)
    return out