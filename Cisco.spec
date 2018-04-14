# -*- mode: python -*-

block_cipher = None


a = Analysis(['Cisco.py'],
             pathex=['/Users/aaron/Documents/github/Cisco-Autocomplete'],
             binaries=[('/Users/aaron/Documents/github/Cisco-Autocomplete/chromedriver', '.')],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
a.datas += [('/img/Cisco_Logo.png', '/Users/aaron/Documents/github/Cisco-Autocomplete/img/Cisco_Logo.png', 'Data')];
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Cisco',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
app = BUNDLE(exe,
             name='Cisco.app',
             icon=None,
             bundle_identifier=None)
