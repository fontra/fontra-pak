# -*- mode: python ; coding: utf-8 -*-
import sys
from importlib.metadata import PackageNotFoundError
from PyInstaller.utils.hooks import collect_all, copy_metadata
from fontra import __version__ as fontraVersion


def buildWindowsVersionResource():
    from PyInstaller.utils.win32.versioninfo import (
        VSVersionInfo,
        FixedFileInfo,
        StringFileInfo,
        StringTable,
        StringStruct,
        VarFileInfo,
        VarStruct,
    )

    y, m, patch, *extra = fontraVersion.split(".", maxsplit=3)
    y, m, patch = [int(v) for v in (y, m, patch)]

    return VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=(y, m, patch, 0),
            prodvers=(y, m, patch, 0),
            mask=0x3F,
            flags=0x0,
            OS=0x4,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo(
                [
                    StringTable(
                        "040904B0",
                        [
                            StringStruct("CompanyName", "Fontra.xyz"),
                            StringStruct("FileDescription", "Fontra Pak"),
                            StringStruct("FileVersion", fontraVersion),
                            StringStruct("InternalName", "Fontra Pak"),
                            StringStruct(
                                "LegalCopyright", "© Google LLC, Just van Rossum"
                            ),
                            StringStruct("OriginalFilename", "Fontra Pak.exe"),
                            StringStruct("ProductName", "Fontra Pak"),
                            StringStruct("ProductVersion", fontraVersion),
                        ],
                    )
                ]
            ),
            VarFileInfo([VarStruct("Translation", [1033, 1200])]),
        ],
    )


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

if sys.platform.startswith("linux"):
    # Matched as filename PREFIXES. The ".so" in each entry is deliberate: it keeps
    # wheel-vendored, hash-suffixed names such as libzstd-44be1190.so.1.5.7 or
    # libjpeg-31e2ca52.so.62.4.0 from being caught, since the wheels' extension
    # modules link against exactly those names.
    SYSTEM_LIB_PREFIXES = (
        # -- C++ / compiler runtime: must match the host's Mesa and GL drivers
        "libstdc++.so",
        "libgcc_s.so",
        # -- GLib family: GIO/GTK modules on the host need the host's glib
        "libglib-2.0.so",
        "libgobject-2.0.so",
        "libgio-2.0.so",
        "libgmodule-2.0.so",
        "libgthread-2.0.so",
        # -- GTK3 stack (pulled in by Qt's libqgtk3.so platform theme)
        "libgtk-3.so",
        "libgdk-3.so",
        "libgdk_pixbuf-2.0.so",
        "libatk-1.0.so",
        "libatk-bridge-2.0.so",
        "libatspi.so",
        "libepoxy.so",
        # -- Text and drawing: must match host fontconfig config syntax
        "libfontconfig.so",
        "libfreetype.so",
        "libcairo.so",
        "libcairo-gobject.so",
        "libpango-1.0.so",
        "libpangocairo-1.0.so",
        "libpangoft2-1.0.so",
        "libharfbuzz.so",
        "libfribidi.so",
        "libgraphite2.so",
        "libthai.so",
        "libdatrie.so",
        "libpixman-1.so",
        "libexpat.so",
        "libbrotlicommon.so",
        "libbrotlidec.so",
        # -- Low-level libs that glib/gio need at a newer version than 22.04 has
        #    (libmount was the cause of "MOUNT_2_40 not found" and of the GTK
        #    file picker silently falling back to Qt's own dialog)
        "libmount.so",
        "libblkid.so",
        "libuuid.so",
        "libselinux.so",
        "libpcre2-8.so",
        "libsystemd.so",
        "libcap.so",
        "libgcrypt.so",
        "libgpg-error.so",
        "libdbus-1.so",
        "libbsd.so",
        "libmd.so",
        # -- Kerberos chain (dependency of the GIO/GTK stack)
        "libgssapi_krb5.so",
        "libkrb5.so",
        "libkrb5support.so",
        "libk5crypto.so",
        "libkeyutils.so",
        "libcom_err.so",
        # -- Keyboard: an old libxkbcommon cannot parse newer Compose files
        #    (the "unrecognized keysym dead_hamza" errors). Prefix covers
        #    libxkbcommon-x11 as well.
        "libxkbcommon",
    )

    # Deliberately NOT excluded (keep bundled):
    #   - libQt6*, libpython3.*, libicu*.73: Qt and Python need their own, and
    #     Fedora ships a different ICU soname
    #   - libjpeg.so.8, libpcre.so.3: newer distros ship different sonames
    #   - hash-suffixed wheel libs (libavif-*, libwebp-*, libtiff-*, ...)
    #   - ABI-stable basics (libz, libpng16, liblz4, libzstd.so.1, libffi, libX11,
    #     libxcb-*): low risk; revisit only if errors point at them

    _before = {b[0] for b in a.binaries}
    a.binaries = [
        b for b in a.binaries
        if not os.path.basename(b[0]).startswith(SYSTEM_LIB_PREFIXES)
    ]
    _removed = sorted(_before - {b[0] for b in a.binaries})
    print(f"[spec] excluded {len(_removed)} system libraries from the bundle:")
    for _name in _removed:
        print(f"[spec]   {_name}")

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
                        "woff",
                        "woff2",
                        "ttx",
                        "designspace",
                        "ufo",
                        "glyphs",
                        "glyphspackage",
                        "fontra",
                        "rcjk",
                        "yaml",
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
        name="Fontra Pak" if sys.platform == "win32" else "fontrapak",
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
        version=buildWindowsVersionResource() if sys.platform == "win32" else None,
    )
