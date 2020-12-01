PDAFT Fontmap Tools
===================

## Installation
1. Install Python 3
2. Run `python -m pip install -r requirements.txt` in a terminal

## Font Modding Guides
Look in guides folder.

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
 - FT/M39s fontmap.bin (direct farc reading not supported)
 - X fontmap.fnm (direct farc reading not supported)
 
 ###### Writing
 - AFT/FT/M39s fontmap.farc
 - Writing X fontmap.farc is experimental

　

#### charlist
 - Outputs a UTF-16 text file containing all characters in the specified font file.
     (`python charlist.py fontmap/font9_24x24.json`)

　

#### generate_font (ALPHA)
 - Generates a font.
     (`python generate_font.py -f [FONT] -o [OUTPUT_NAME] -s [SIZE]`, detailed usage with `-h`)
 
 ##### Notes
 - The tool has had very little testing
 - Proportional (non-fixed width) fonts may give bad results
 - It could really use a fallback mechanism for missing characters
 - If you can't load font files, copy the ttf/ttc/??? into the fontmap tools directory and specify the exact filename of the font

　

#### PD Loader Patches (ALPHA)
 - font_res_support.p enables support for fonts without metrics matching the original font they replace (including HD fonts)
 - proportional_main_font.p enables proportional character width on the two main 24px fonts
 - separate_fonts.p makes the non-bold 24px font use font id 15