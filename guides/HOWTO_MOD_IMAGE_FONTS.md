How To Mod Image Fonts (Beginners Guide)
========================================

Currently, only AFT, FT, and M39s fontmaps can be generated.
The guide focuses on AFT, but most of it should work with the other games too.

"Image fonts" refers to stuff like the stylised numbers used for scores.
They must be manually generated.

1. Extract original fontmap  
   **For AFT:** `python fontmap_extract.py fontmap.farc`  
   **For other games:** Extract fontmap.bin with Farcpack or MMM, then `python fontmap_extract.py fontmap.bin`
2. Create your bitmap sheet of characters  
   All characters should be in a neat, evenly-spaced grid for this to work properly.
   Start at the top-left corner, going left-to-right then top-to-bottom.
   Ideally you should put characters in the same order as the original font.  
   It's also possible to generate a font using a custom charlist as a starting point and apply styles/effects to that.
   (use the shrink option to make space for your effects if using a generated font)
3. Find the JSON of the font you're replacing  
   The easiest way is by looking at the font sizes.
4. Edit the JSON  
   `box_width` and `box_height` should be set to your grid size.  
   `advance_width` and `line_height` will adjust spacing. Set them to about the width and height of one character.  
   `tex_size_chars` is the number of characters on one row of the texture.  
   In each character, `codepoint` is the unicode encoding of the character, `halfwidth` should be false,  
   and `glyph_x` and `glyph_width` probably don't matter.  
   (if using a newly-generated font, just replace the entire JSON contents except for the original id)
5. Rebuild fontmap
   `python fontmap_extract.py fontmap` (will turn folder contents into a farc)
6. Replace textures
   Use the replace flipped option in MikuMikuModel. The fonts are in `spr_fnt_XX`.