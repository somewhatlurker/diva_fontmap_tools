PDAFT Fontmap Tools
===================

## Installation
1. Install Python 3
2. Run `python -m pip install -r requirements.txt` in a terminal

## Tools
#### fontmap_extract
 ##### Usage
 - Extract an fontmap to directory with matching name: `python fontmap_extract.py fontmap.farc`
     (creates JSON files in directory fontmap)
 - Build an AFT fontmap from a directory: `python fontmap_extract.py dir_name`
     (creates dir_name.farc)
 
 ##### Format Support
 ###### Reading
 - AFT fontmap.farc or fontmap.bin
 - X fontmap.fnm (direct farc reading not supported)
 
 ###### Writing
 - AFT fontmap.farc

　

#### charlist
 - Outputs a UTF-16 text file containing all characters in the specified font file.
     (`python utils/charlist.py fontmap/font9_24x24.json`)