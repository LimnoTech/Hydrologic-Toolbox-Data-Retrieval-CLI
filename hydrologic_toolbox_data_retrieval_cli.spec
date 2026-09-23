# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/hydrologic_toolbox_data_retrieval_cli/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'hydrologic_toolbox_data_retrieval_cli.app',
        'hydrologic_toolbox_data_retrieval_cli.cli',
        'hydrologic_toolbox_data_retrieval_cli.config',
        'hydrologic_toolbox_data_retrieval_cli.exports',
        'hydrologic_toolbox_data_retrieval_cli.frame_types',
        'hydrologic_toolbox_data_retrieval_cli.station_discovery',
        'hydrologic_toolbox_data_retrieval_cli.timeseries',
        'hydrologic_toolbox_data_retrieval_cli.xml_compat',
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
    name='hydrologic_toolbox_data_retrieval_cli',
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
    name='hydrologic_toolbox_data_retrieval_cli',
)
