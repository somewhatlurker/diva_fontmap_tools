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

The positioning of characters within the grid can be set manually with `--force_baseline 0.XX` if necessary.
0.85 should be a good starting point.

Characters can be forced to use less of the available space with `--shrink X` set to the amount of pixels to shrink by.

To set a custom character list (what characters to output), add `-c [CHARLIST_TXT]`.

For help selecting a font style/variation from a font with multiple in a single file, read `font_variations.md`.

　

You can use `-h` for a quick reference.

　

### Fallbacks
It's possible to make a chain of fonts to fill in missing characters from your main font(s).  
To facilitate this, `-f`, `-i`, `-v`, and `--shrink` can accept comma-separated lists.

When one option contains a list, all others must also (if they're used).  
While convoluted this makes it possible to create full fonts using characters from incomplete fonts.

It may take some tweaking of the baseline and shrink settings to find something that looks right.

Example: `generate_font.py -f "comicsans\comic.ttf,uddigikyokasho\UDDigiKyokashoN-R.ttc,bizudgothic\BIZ-UDGothicR.ttc" -i 0,1,1 --shrink 3,1,1 -o comicsans\comicsans -s 36 --force_baseline 0.81`

Try not to worry too much if there's still a few characters missing after adding fallbacks.

　

### Sega-Style Proportional
`--sega_style_proportional` can be used to add proportional rendering information to fixed width fonts.
This is useful for mods that should work on both Japanese and English versions of games because it will render well
in both fixed width and proportional modes, like the original fonts.

It may also be useful to try using it if a font renders with weird spacing.