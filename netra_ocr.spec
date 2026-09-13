# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# 1. Force collect EVERYTHING for tkinter, customtkinter, and torchvision
datas_tk, binaries_tk, hiddenimports_tk = collect_all('tkinter')
datas_ctk, binaries_ctk, hiddenimports_ctk = collect_all('customtkinter')
datas_tv, binaries_tv, hiddenimports_tv = collect_all('torchvision')

# 2. CRITICAL FIX: Collect all data files (like .pt model weights) from netra_ocr
datas_netra = collect_data_files('netra_ocr', include_py_files=False)

# 3. Explicitly add your local project modules to hidden imports
local_hidden_imports = [
    'core',
    'core.document_handler',
    'core.ocr_worker',
    'ui',
    'ui.markdown_widget',
    'utils',
    'utils.exporter',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'fitz',
    'pymupdf',
    'netra_ocr',
    'netra_ocr.ocr_engine',
    'netra_ocr.detectors.yolo', # Ensure YOLO detector hooks are triggered
]

a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=binaries_tk + binaries_ctk + binaries_tv,
    datas=[('src', 'src')] + datas_tk + datas_ctk + datas_tv + datas_netra,
    hiddenimports=hiddenimports_tk + hiddenimports_ctk + hiddenimports_tv + local_hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # ✅ Add heavy, unused PyTorch modules to excludes to save space
    excludes=[
        'test', 'tests',
        'torch.distributed',
        'torch.testing',
        'torch.onnx',
        'torch.fx',
        'torch.utils.bottleneck',
        'torch.backends.cuda', # We are using CPU-only anyway
    ],
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
            'CFBundleShortVersionString': '0.0.1',
            'CFBundleVersion': '0.0.1',
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