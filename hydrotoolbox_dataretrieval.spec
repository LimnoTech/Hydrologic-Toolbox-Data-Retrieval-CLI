# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/hydrotoolbox_dataretrieval/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'hydrotoolbox_dataretrieval.app',
        'hydrotoolbox_dataretrieval.cli',
        'hydrotoolbox_dataretrieval.config',
        'hydrotoolbox_dataretrieval.exports',
        'hydrotoolbox_dataretrieval.frame_types',
        'hydrotoolbox_dataretrieval.station_discovery',
        'hydrotoolbox_dataretrieval.timeseries',
        'hydrotoolbox_dataretrieval.xml_compat',
        'hydrotoolbox_dataretrieval._version',
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
    [],
    exclude_binaries=True,
    name='hydrotoolbox_dataretrieval',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='hydrotoolbox_dataretrieval',
)
