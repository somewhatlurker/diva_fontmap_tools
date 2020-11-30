# separate bold and normal fonts
140185477:e9 25 ff ff ff  // JMP  0x1401853a1

1401853a1:c6 44 24 38 02  // MOV  byte ptr [RSP + 0x38],0x2
1401853a6:c6 44 24 30 01  // MOV  byte ptr [RSP + 0x30],0x1
1401853ab:e9 cd 00 00 00  // JMP 0x14018547d

14018547d:c7 44 24 40 0f 00 00 00  // MOV  dword ptr [RSP + 0x40],0xf