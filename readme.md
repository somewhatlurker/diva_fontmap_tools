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
     (`python charlist.py fontmap/font9_24x24.json`)

　

#### generate_font (ALPHA)
 - Generates a font.
     (`python generate_font.py -f [FONT] -o [OUTPUT_NAME] -s [SIZE]`, detailed usage with `-h`)
 
 ##### Guide
 1. Extract original fontmap
     - Use fontmap_extract as shown above
 2. Generate your bold font
     - Use `-v [VARIATION]` to select it if it shares a source file with other variations
         `--list_variations` will show possibe options
     - `-i` may be required for ttc files
 3. Open your bold font's json output and write down `[advance_width],[line_height],[box_width],[box_height]`
     (eg. `24,24,26,26`)
 4. Generate your normal font, using the bold font's metrics in `-m` (eg. `-m 24,24,26,26`)
 5. Replace the main font json (`font9_24x24.json` for AFT) with your bold font's json
 6. Rebuild fontmap.farc
     - Use fontmap_extract as shown above
 7. Replace flipped textures using MikuMikuModel in `spr_fnt_***`.
 
 ##### Notes
 - The tool has had very little testing
 - Proportional (non-fixed width) fonts may give bad results
 - It could really use a fallback mechanism for missing characters

　

#### font_res_support.p (ALPHA)
 - PD Loader patch needed for fonts without metrics matching the original font they replace
 - Unknown if it'll work with HD fonts