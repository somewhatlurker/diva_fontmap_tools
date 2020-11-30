Generating Fonts
================

To generate a font, use the generate_font tool: `python generate_font.py -f [FONT] -o [OUTPUT_NAME] -s [SIZE]`

`FONT` should be the filename of a font (not the display name). If you have trouble loading fonts, try copying
the font file into the same directory you're running the tool from.

`OUTPUT_NAME` is the name to give output files (eg. `myfont` or `myfontbold`).

`SIZE` is the desired font size.

For games without custom font resolution patches, or to match an already-generated font's sizing info,
make sure you set the same font size and add `-m [advance_width],[line_height],[box_width],[box_height]`
(eg. `-m 24,24,26,26`) to the command line.
(`advance_width`, `line_height`, `box_width`, and `box_height` are from `fontXX_XXxXX.json`)

To set a custom character list (what characters to output), add `-c [CHARLIST_TXT]`.

For help selecting a font style/variation from a font with multiple in a single file, read `font_variations.md`.

　

You can use `-h` for a quick reference.