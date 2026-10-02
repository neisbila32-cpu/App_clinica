# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('D:/app_clinica/venv/Lib/site-packages/customtkinter', 'customtkinter'), ('welcome_nutrilab.png', '.'), ('clinica.db', '.'), ('regras_exames_complementares.json', '.'), ('exames_internos', 'exames_internos'), ('condutas_internas', 'condutas_internas'), ('sintomas_internos', 'sintomas_internos'), ('prescricoes_internas', 'prescricoes_internas')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='app_clinica',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app_clinica',
)
