# Load font res info from fontmap
14018783f:e9 b0 03 00 00 // JMP 0x140187bf4

140187bf4:e8 27 02 00 00 // CALL FUN_140187e20
140187bf9:48 8b 46 04    // MOV RAX, qword ptr [RSI + 0x04]
140187bfd:eb 17          // JMP 0x140187c16

140187c16:49 89 46 dc    // MOV qword ptr [R14 + -0x24], RAX
140187c1a:e9 25 fc ff ff // JMP 0x140187844