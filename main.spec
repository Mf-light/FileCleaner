# -*- mode: python ; coding: utf-8 -*-
# FileCleaner 打包配置 - onedir 模式（用于制作安装包）


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources/app.ico', 'resources')],
    hiddenimports=['PyQt6', 'pywin32', 'win32com', 'pythoncom', 'win32com.shell', 'win32com.client'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FileCleaner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FileCleaner',
)
