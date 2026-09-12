# 🇰🇭 Netra Khmer OCR Desktop

A complete, offline, multiplatform desktop application for Khmer Optical Character Recognition, powered by the
**Netra-OCR** engine and built with a modern, intuitive UI.

## ✨ Features

- **Specialized Khmer OCR**: High-accuracy recognition for Khmer and bilingual text.
- **Multi-format Input**: Supports scanned PDFs and images (PNG, JPG, JPEG, BMP, TIFF).
- **Flexible Export**: Export results to `.txt`, `.md`, `.docx`, and `.xlsx`.
- **Customizable Display**: Toggle line numbers and estimated accuracy percentages via the Settings menu.
- **Modern, Intuitive UI**: Clean, icon-driven interface designed for clarity.
- **100% Offline**: After the initial model download, all processing happens locally.

## 🛠️ Installation & Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/netra-ocr-desktop.git
   cd netra-ocr-desktop
2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows: venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```
3. Install dependencies:
    ```bash
   pip install -r requirements.txt
    ```
4. Run the application:
    ```bash
   python src/app.py
    ```

_Note on First Run: The first time you process an image, the app will automatically download the ~77MB Netra-OCR model
weights via Hugging Face and cache them locally. Subsequent runs are 100% offline._

### 📦 Building for Distribution

The project includes GitHub Actions to automatically build standalone executables for Windows, macOS, and Linux using
PyInstaller.
To build locally:

```bash
   # Windows
    pyinstaller --noconfirm --onefile --windowed --name "NetraKhmerOCR" --add-data "src;src" src/app.py
    # macOS / Linux
    pyinstaller --noconfirm --onefile --windowed --name "NetraKhmerOCR" --add-data "src:src" src/app.py
```

The compiled executable will be located in the dist/ directory.

### 🤝 Contributing

Please read our [Contributing Guidelines](.github/CONTRIBUTE.md) for details on our GitFlow workflow and code submission
process.

## 🙏 Credits & Acknowledgments

This desktop application is built upon the powerful **Netra-OCR** engine. We extend our deepest gratitude to the **Netra
AI Lab** and the original authors for their groundbreaking work in Khmer Optical Character Recognition.

- **Original Engine:** [Netra-OCR GitHub Repository](https://github.com/netra-ai-lab/Netra-OCR)
- **Research
  Paper:** [A Squeeze-and-Excitation Transformer Network for Khmer OCR](https://github.com/netra-ai-lab/Netra-OCR)
- **Model
  Weights:** [Hugging Face - Darayut/khmer-text-recognition](https://huggingface.co/Darayut/khmer-text-recognition)

Without their open-source contribution and research, this application would not be possible.

---

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🚀 How to Initialize in PyCharm

1. Open PyCharm and select **New Project**.
2. Name it `netra-ocr-desktop` and ensure a **New Virtual Environment** is selected.
3. Create the folder structure exactly as shown above.
4. Copy and paste the contents of each file into the respective files in PyCharm.
5. Open the terminal in PyCharm (`Alt + F12`) and run: `pip install -r requirements.txt`
6. Right-click `src/app.py` and select **Run 'app'**.

This setup gives you a professional, CI/CD-ready, multiplatform desktop application project that adheres to modern
Python best practices.

