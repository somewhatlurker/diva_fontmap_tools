PDAFT Fontmap Tool
==================

### Installation
1. Install Python 3
2. Run `python -m pip install -r requirements.txt` in a terminal

### Usage
- Extract an fontmap to directory with matching name: `python fontmap_tool.py fontmap.farc`
    (creates JSON files in directory fontmap)
- Build an AFT fontmap from a directory: `python fontmap_tool.py dir_name`
    (creates dir_name.farc)

### Format Support
##### Reading
- AFT fontmap.farc or fontmap.bin
- X fontmap.fnm (direct farc reading not supported)

##### Writing
- AFT fontmap.farc