# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[('C:\\Users\\Joseph Choi\\AppData\\Roaming\\Python\\Python314\\site-packages\\llama_cpp\\lib\\ggml-base.dll', 'llama_cpp\\lib'), ('C:\\Users\\Joseph Choi\\AppData\\Roaming\\Python\\Python314\\site-packages\\llama_cpp\\lib\\ggml-cpu.dll', 'llama_cpp\\lib'), ('C:\\Users\\Joseph Choi\\AppData\\Roaming\\Python\\Python314\\site-packages\\llama_cpp\\lib\\ggml.dll', 'llama_cpp\\lib'), ('C:\\Users\\Joseph Choi\\AppData\\Roaming\\Python\\Python314\\site-packages\\llama_cpp\\lib\\llama.dll', 'llama_cpp\\lib'), ('C:\\Users\\Joseph Choi\\AppData\\Roaming\\Python\\Python314\\site-packages\\llama_cpp\\lib\\mtmd.dll', 'llama_cpp\\lib')],
    datas=[],
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
    name='DICOM-Classifier',
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
    name='DICOM-Classifier',
)
