# forge.spec
# ──────────────────────────────────────────────────────────
#  Script de build para gerar forge.exe com PyInstaller
#
#  Como usar:
#    pip install pyinstaller flask
#    pyinstaller forge.spec
#
#  O executável estará em: dist/forge/forge.exe  (Windows)
#                           dist/forge/forge      (Linux/Mac)
# ──────────────────────────────────────────────────────────

block_cipher = None

a = Analysis(
    ['forge_server.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Inclui toda a pasta static no bundle
        ('static', 'static'),
    ],
    hiddenimports=[
        'flask',
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.routing',
        'werkzeug.exceptions',
        'werkzeug.middleware',
        'jinja2',
        'click',
        'itsdangerous',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='forge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,          # False = sem janela de console (Windows)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,             # Coloque 'forge.ico' aqui para ícone personalizado
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='forge',
)
