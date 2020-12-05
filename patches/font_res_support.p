# Load font res info from fontmap
14018783f:e9 b0 03 00 00 // JMP 0x140187bf4

140187bf4:e8 27 02 00 00 // CALL FUN_140187e20
140187bf9:48 8b 46 04    // MOV RAX, qword ptr [RSI + 0x04]
140187bfd:eb 17          // JMP 0x140187c16

140187c16:49 89 46 dc    // MOV qword ptr [R14 + -0x24], RAX
140187c1a:e9 25 fc ff ff // JMP 0x140187844


// get new font data for dwgui after loading fontmap
// ideally I should destruct old stuff too, but it's not strictly necessary and I'm lazy
140187ee8:b0 01 48 83 c4 20 5b c3  // relocated from 0x140187ee4
140187ec6:75 20                    // fix JNZ target for above

140187edc:e8 4f 9e 17 00  // CALL  0x140301d30 (regenerate fonts)
140187ee1:e8 9a a6 17 00  // CALL  0x140302580 (regenerate menu)
140187ee6:eb 9e           // JMP  0x140187e86

140187e86:32 c0 48 83 c4 20 5b c3  // relocated from 0x140187edc
140187ebd:75 c7                    // fix JNZ target for above