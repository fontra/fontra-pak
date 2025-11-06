# -*- mode: python ; coding: utf-8 -*-
import sys
from importlib.metadata import PackageNotFoundError
from PyInstaller.utils.hooks import collect_all, copy_metadata
from fontra import __version__ as fontraVersion

datas = []
binaries = []
hiddenimports = []

modules_to_collect_all = [
    "fontra",
    "fontra_compile",
    "fontra_glyphs",
    "fontra_rcjk",
    "cffsubr",
    "openstep_plist",
    "glyphsLib.data",
]
for module_name in modules_to_collect_all:
    tmp_ret = collect_all(module_name)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
    try:
        datas += copy_metadata(module_name)
    except PackageNotFoundError:
        print("no metadata for", module_name)


block_cipher = None


a = Analysis(
    ["FontraPakMain.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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

if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="Fontra Pak",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch="universal2",
        codesign_identity=None,
        entitlements_file=None,
        icon="icon/FontraIcon.ico",
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="Fontra Pak",
    )
    app = BUNDLE(
        coll,
        name="Fontra Pak.app",
        icon="icon/FontraIcon.icns",
        bundle_identifier="xyz.fontra.fontra-pak",
        version=fontraVersion,
        info_plist={
            "CFBundleDocumentTypes": [
                dict(
                    CFBundleTypeExtensions=[
                        "ttf",
                        "otf",
                        "designspace",
                        "ufo",
                        "glyphs",
                        "fontra",
                        "rcjk",
                    ],
                    CFBundleTypeRole="Editor",
                ),
            ],
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="Fontra Pak",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon="icon/FontraIcon.ico",
    )
