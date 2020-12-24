# -*- mode: python ; coding: utf-8 -*-

from os.path import abspath

pathex = abspath(SPECPATH)

block_cipher = None


fontmap_extract_a = Analysis(['fontmap_extract.py'],
             pathex=[pathex],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

charlist_a = Analysis(['charlist.py'],
             pathex=[pathex],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

generate_font_a = Analysis(['generate_font.py'],
             pathex=[pathex],
             binaries=[],
             datas=[ ('misc/charlist.txt', 'misc') ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

MERGE( (fontmap_extract_a, 'fontmap_extract', 'fontmap_extract'),
        (charlist_a, 'charlist', 'charlist'),
        (generate_font_a, 'generate_font', 'generate_font') )


fontmap_extract_pyz = PYZ(fontmap_extract_a.pure, fontmap_extract_a.zipped_data,
             cipher=block_cipher)
fontmap_extract_exe = EXE(fontmap_extract_pyz,
          fontmap_extract_a.scripts,
          [],
          exclude_binaries=True,
          name='fontmap_extract',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
fontmap_extract_coll = COLLECT(fontmap_extract_exe,
               fontmap_extract_a.binaries,
               fontmap_extract_a.zipfiles,
               fontmap_extract_a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='fontmap_extract')


charlist_pyz = PYZ(charlist_a.pure, charlist_a.zipped_data,
             cipher=block_cipher)
charlist_exe = EXE(charlist_pyz,
          charlist_a.scripts,
          [],
          exclude_binaries=True,
          name='charlist',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
charlist_coll = COLLECT(charlist_exe,
               charlist_a.binaries,
               charlist_a.zipfiles,
               charlist_a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='charlist')


generate_font_pyz = PYZ(generate_font_a.pure, generate_font_a.zipped_data,
             cipher=block_cipher)
generate_font_exe = EXE(generate_font_pyz,
          generate_font_a.scripts,
          [],
          exclude_binaries=True,
          name='generate_font',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
generate_font_coll = COLLECT(generate_font_exe,
               generate_font_a.binaries,
               generate_font_a.zipfiles,
               generate_font_a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='generate_font')