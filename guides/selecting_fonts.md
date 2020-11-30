Selecting Fonts
===============

The Project DIVA games are designed to work with fixed width fonts.  
In addition, the fontmap generator currently requires fonts to support Japanese for good results.
Fonts without Japanese characters will likely have incorrect spacing and be missing characters.

With patches to the game, proportional (non-fixed width) font support can be enabled.
The included `proportional_main_font.p` patch does this for AFT's main 24px fonts.

　

To tell whether your font is fixed width or proportional, write out a line of English text and another line filled with
dots so that the number of dots is the same as the number of letters (eg. `Hatsune Miku` (12 letters), `............`).
If the lines are exactly the same length and letters are perfectly aligned with the dots, the font is fixed width.

　

It is actually possible to use a proportional font in games that don't support it, but the character spacing may be bad.
Feel free to try your exact font and see what happens.