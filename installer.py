import os
import sys
import subprocess
import shutil
from pathlib import Path

INSTALL_DIR = Path.home() / ".netra_ocr"
MODEL_DIR = INSTALL_DIR / "models"
LAUNCHER_SH = INSTALL_DIR / "run_netra_ocr.sh"
LAUNCHER_BAT = INSTALL_DIR / "run_netra_ocr.bat"


def download_model():
    """Downloads the Netra-OCR model to the local cache."""
    print("📥 Downloading Netra-OCR model (this may take a few minutes)...")
    try:
        from huggingface_hub import snapshot_download
        # Download the specific model repo to our local directory
        snapshot_download(
            repo_id="Darayut/khmer-text-recognition",
            local_dir=str(MODEL_DIR),
            local_dir_use_symlinks=False
        )
        print("✅ Model downloaded successfully!")
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        print("Please check your internet connection and try again.")
        sys.exit(1)


def create_launcher():
    """Creates platform-specific launcher scripts."""
    app_path = Path(__file__).parent / "src" / "app.py"

    # Bash launcher (Mac/Linux)
    with open(LAUNCHER_SH, "w") as f:
        f.write(f"""#!/bin/bash
export NETRA_OCR_MODEL_DIR="{MODEL_DIR}"
python3 "{app_path}"
""")
    os.chmod(LAUNCHER_SH, 0o755)

    # Batch launcher (Windows)
    with open(LAUNCHER_BAT, "w") as f:
        f.write(f"""@echo off
set NETRA_OCR_MODEL_DIR={MODEL_DIR}
python "{app_path}"
""")

    print(f"🚀 Launchers created in {INSTALL_DIR}")
    print("   - Mac/Linux: Run './run_netra_ocr.sh'")
    print("   - Windows: Run 'run_netra_ocr.bat'")


def main():
    print("🇰🇭 Netra OCR Offline Installer")
    print("=" * 40)

    # Create directories
    INSTALL_DIR.mkdir(exist_ok=True)
    MODEL_DIR.mkdir(exist_ok=True)

    # Check if model exists
    model_files = list(MODEL_DIR.glob("*.pth"))
    if not model_files:
        download_model()
    else:
        print("✅ Model already exists. Skipping download.")

    create_launcher()
    print("\n🎉 Installation complete! You can now run Netra OCR offline.")


if __name__ == "__main__":
    main()