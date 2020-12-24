PDAFT Fontmap Tools
===================

## Installation
1. Install Python 3.8+ -- use a venv if you want
2. Run `python -m pip install -r requirements.txt` in a terminal
3. (Optional) Run `python -m pip install gooey` if you want GUI support in generate_font

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
 - FT/M39s fontmap.farc or fontmap.bin
 - X fontmap_fnm.farc or fontmap.fnm
 
 ###### Writing
 - AFT/FT/M39s fontmap.farc
 - Writing X fontmap.farc is experimental

　

#### charlist
 - Outputs a UTF-16 text file containing all characters in the specified font file.
     (`python charlist.py fontmap/font9_24x24.json`)

　

#### generate_font (ALPHA)
 - Generates a font.
     (`python generate_font.py -f [FONT] -o [OUTPUT_NAME] -s [SIZE]`, detailed usage with `-h`)
     (or run with no output set for a GUI if you installed GUI support)
 
 ##### Notes
 - The tool has had very little testing
 - Proportional (non-fixed width) fonts may give bad results
 - If you can't load font files, copy the ttf/ttc/??? into the fontmap tools directory and specify the exact filename of the font

　

#### PD Loader Patches (ALPHA)
 - font_res_support.p enables support for fonts without metrics matching the original font they replace (including HD fonts)
 - proportional_main_font.p enables proportional character width on the two main 24px fonts
 - separate_fonts.p makes the non-bold 24px font use font id 15

## Development Info
License is MIT so do whatever you want, but I'd personally prefer if we avoid forks for now.

Diva file formats are handled by pydiva. Check there to get an idea of what's going on.

Font related stuff is kinda messy tbh, and could do with some cleanup, but most of the stuff was added in response to
specific issues so please don't go changing or removing anything unless you test it well or know what you're doing.

As for in-game stuff for patch development, TLAC's `Drawing.h` and `Drawing.cpp` from the main PD Loader repo have the
important structs documented pretty well and some functions that'll get you into the important stuff if you just dig
down into them.