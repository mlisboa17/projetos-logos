# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Configuração do PyInstaller para o scraper Vibra standalone

a = Analysis(
    ['scraper_standalone.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'playwright',
        'playwright.sync_api',
        'requests',
        'json',
        'datetime',
        'time',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'django',
        'numpy',
        'matplotlib',
        'pandas',
        'tensorflow',
        'torch',
        'opencv'
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ScraperVibra',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)