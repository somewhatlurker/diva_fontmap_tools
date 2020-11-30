Font Variations
===============

Usually, choosing font styles just involves loading a different file, but some fonts merge several styles into one file.
There are two ways to select variations, depending on the font file:

For .ttc fonts, add `-i X` to the generate_font command line, where X is the font number within the file
(use trial-and-error to find the correct font based on command line output)

For other fonts, run generate_font with `--list_variations`, then copy the name of the variation you want and use it
with `-v [VARIATION]` when generating your font.