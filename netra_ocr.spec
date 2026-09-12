# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None

a = Analysis(
    ['src/app.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src')],
    hiddenimports=[],
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

# Check the platform to apply the correct build strategy
if sys.platform == 'darwin':
    # ==========================================
    # macOS: Create a proper .app bundle (Folder)
    # ==========================================
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True, # Must be True for BUNDLE
        name='NetraOCR',
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
        icon=None, # Icon is handled by BUNDLE
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='NetraOCR',
    )

    app = BUNDLE(
        coll,
        name='NetraOCR.app',
        icon='assets/icon.icns',
        bundle_identifier='com.netra.ocr',
        info_plist={
            'CFBundleName': 'Netra OCR',
            'CFBundleDisplayName': 'Netra OCR',
            'NSHighResolutionCapable': True,
        },
    )

else:
    # ==========================================
    # Windows/Linux: Create a single .exe file
    # ==========================================
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='NetraOCR',
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
        icon='assets/icon.ico', # Windows icon
    )