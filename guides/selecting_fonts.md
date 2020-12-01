Selecting Fonts
===============

For best results it is recommended to use fonts with good Japanese support, but it's possible to get decent results
using English fonts and Japanese fallback fonts for missing characters.  
Fonts without Japanese support will have lots of missing characters if used without a Japanese fallback.

Additionally, non-English versions of the games are designed to work with fixed width fonts only,
but the English versions seem to have proportional (non-fixed width) font support enabled.

Non-English versions can be patched to enable proportional font support.  
The included `proportional_main_font.p` patch does this for AFT's main 24px fonts.

　

To tell whether your font is fixed width or proportional, write out a line of English text and another line filled with
dots so that the number of dots is the same as the number of letters (eg. `Hatsune Miku` (12 letters), `............`).
If the lines are exactly the same length and letters are perfectly aligned with the dots, the font is fixed width.

　

It is actually possible to use a proportional font in games that don't support it, but the character spacing may be bad.
Feel free to try your exact font and see what happens.