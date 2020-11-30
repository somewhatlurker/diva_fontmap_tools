How To Mod Main Text Fonts (Beginners Guide)
============================================

Currently, only AFT, FT, and M39s fontmaps can be generated.
The guide focuses on AFT, but most of it except for font numbers and IDs should work with the other games too.

Before starting, read through `selecting_fonts.md` to help with choosing a font to use.

1. Extract original fontmap  
   **For AFT:** `python fontmap_extract.py fontmap.farc`  
   **For other games:** Extract fontmap.bin with Farcpack or MMM, then `python fontmap_extract.py fontmap.bin`
2. Generate a bold font  
   See `generating_fonts.md` for info.
   Use `charlist_m39s.txt` as the charlist for games that aren't AFT.
3. Generate a regular font  
   **For AFT:** If you patch the game to have separate fontmaps (patch not yet released), you can generate an entirely different font.  
   Without a patch, you should only use the same font as used for the bold one (but the non-bold version),
   and copy the sizing info from the generated bold font as explained in `generating_fonts.md`.
   (using two different fixed width fonts may also work well, but is untested)  
   **For other games:** I think they already use a separate fontmaps, but I don't know for sure.
4. Replace font JSON files  
   **For AFT:** The main font is `font9_24x24.json`, and the font inside has id `0`.
   Replace it with your generated bold fontmap, and set the id inside to `0` so it matches the original font.  
   If you patch the game to have separate fontmaps, copy your regular font to `font16.json` and set the id to `15`.
   **For other games:** Check `font_numbers.md` for known info (information may be incorrect)
5. Rebuild fontmap  
   `python fontmap_extract.py fontmap` (will turn folder contents into a farc)
6. Replace textures  
   Use the replace flipped option in MikuMikuModel. The fonts are in `spr_fnt_XX`.