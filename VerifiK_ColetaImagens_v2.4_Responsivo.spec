# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para VerifiK Sistema de Coleta v2.4
# Versão com correções de responsividade

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Coleta todas as DLLs necessárias do OpenCV e NumPy
opencv_binaries = collect_dynamic_libs('cv2')
numpy_binaries = collect_dynamic_libs('numpy')

a = Analysis(
    ['sistema_coleta_standalone_v2.py'],
    pathex=[],
    binaries=opencv_binaries + numpy_binaries,
    datas=[],
    hiddenimports=[
        'PIL._tkinter_finder',
        'PIL._imagingtk',
        'PIL.ImageTk',
        'numpy.core._multiarray_umath',
        'cv2',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='VerifiK_ColetaImagens_v2.4_Responsivo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Desabilita UPX para evitar problemas com DLLs
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
