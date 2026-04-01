# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/waterdata_toolbox_demo/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'waterdata_toolbox_demo.app',
        'waterdata_toolbox_demo.cli',
        'waterdata_toolbox_demo.config',
        'waterdata_toolbox_demo.exports',
        'waterdata_toolbox_demo.gui',
        'waterdata_toolbox_demo.plotting',
        'waterdata_toolbox_demo.station_discovery',
        'waterdata_toolbox_demo.timeseries',
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
    name='waterdata_toolbox_demo',
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
    name='waterdata_toolbox_demo',
)
