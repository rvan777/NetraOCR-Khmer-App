import pymupdf  # PyMuPDF
from PIL import Image
import io


class DocumentHandler:
    def __init__(self):
        self.doc = None
        self.is_pdf = False
        self.total_pages = 0
        self.file_path = None

    def load_document(self, path):
        self.file_path = path
        self.is_pdf = path.lower().endswith('.pdf')
        if self.is_pdf:
            self.doc = pymupdf.open(path)
            self.total_pages = len(self.doc)
        else:
            self.doc = None
            self.total_pages = 1

    def _pixmap_to_pil(self, pix):
        """
        Bulletproof conversion from PyMuPDF Pixmap to PIL Image.
        Uses an in-memory PNG bridge to handle ALL colorspaces (CMYK, Gray, RGBA) flawlessly.
        """
        # Encode to PNG in memory (handles all color/alpha conversions natively)
        png_data = pix.tobytes("PNG")
        # Open with PIL and force to RGB for the OCR engine
        return Image.open(io.BytesIO(png_data)).convert("RGB")

    def get_page_image(self, page_num, dpi=150):
        """Extracts a page directly into a PIL Image in memory."""
        if self.is_pdf:
            page = self.doc.load_page(page_num)
            pix = page.get_pixmap(dpi=dpi)
            return self._pixmap_to_pil(pix)
        else:
            return Image.open(self.file_path).convert("RGB")

    def get_preview_image(self, page_num, max_w=400, max_h=480):
        """Generates a resized preview image for the UI."""
        if self.is_pdf:
            page = self.doc.load_page(page_num)
            pix = page.get_pixmap(dpi=120)
            img = self._pixmap_to_pil(pix)
        else:
            img = Image.open(self.file_path).convert("RGB")

        img.thumbnail((max_w, max_h))
        return img

    def close(self):
        if self.doc:
            self.doc.close()
            self.doc = None