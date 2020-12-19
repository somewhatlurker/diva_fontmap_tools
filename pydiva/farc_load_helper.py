"""
Helper for when you want to load a file that may or may not be inside a farc archive.
"""

from pydiva import pyfarc

def farc_load_helper(s, filenames):
    """
    Takes a stream and list of desired files, returns a list of tuples [(filename, bytes)]
    If stream s does not contain a supported farc file, returns original bytes with filenamee None.
    Otherwise, opens the archive and returns the requested files if present.
    (files not present in the archive will be ignored)
    """
    
    try:
        farc = pyfarc.from_stream(s)
    except pyfarc.UnsupportedFarcTypeException:
        return [(None, s.read())]
    
    outlist = []
    for fname in filenames:
        if fname in farc['files']:
            outlist += [(fname, farc['files'][fname]['data'])]
    
    return outlist