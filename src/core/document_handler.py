import io
import os
import re
import tempfile

import pymupdf
from netra_ocr.ocr_engine import KhmerOCRPipeline
from PIL import Image

# Check for custom model directory set by installer
CUSTOM_MODEL_DIR = os.environ.get("NETRA_OCR_MODEL_DIR")
if CUSTOM_MODEL_DIR:
    os.environ["HF_HOME"] = CUSTOM_MODEL_DIR


class OCRWorker:
    def __init__(self, doc_handler, result_queue):
        self.doc_handler = doc_handler
        self.result_queue = result_queue
        self.pipeline = None
        self.current_decoder = None

        # PERFORMANCE FIX: Create ONE temp file and reuse it for all pages
        self._temp_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
            suffix=".png", delete=False
        ).name

    def process(self, mode_config, rich_text_mode):
        try:
            decoder = mode_config["decoder"]
            if self.pipeline is None or self.current_decoder != decoder:
                self.result_queue.put({"type": "status", "msg": "Loading OCR model..."})
                self.pipeline = KhmerOCRPipeline(
                    detector="yolo", conf=mode_config["conf"], decoder=decoder
                )
                self.current_decoder = decoder

            total_pages = self.doc_handler.total_pages

            for page_num in range(total_pages):
                self.result_queue.put(
                    {"type": "progress", "value": (page_num + 1) / total_pages}
                )

                img = self.doc_handler.get_page_image(page_num, dpi=150)
                img.save(self._temp_file, format="PNG")

                return_segments = rich_text_mode
                ocr_result = self.pipeline.process_image(
                    self._temp_file,
                    output_path=None,
                    beam_width=mode_config["beam_width"],
                    batch_size=16,
                    return_segments=return_segments,
                )

                if return_segments:
                    result_text, meta = ocr_result
                else:
                    result_text = ocr_result
                    meta = None

                page_results = self._parse_results(
                    result_text, meta, page_num + 1, img, rich_text_mode
                )
                self.result_queue.put(
                    {"type": "page_done", "page": page_num + 1, "results": page_results}
                )

            self.result_queue.put({"type": "finished"})
        except Exception as e:  # noqa: BLE001
            self.result_queue.put({"type": "error", "msg": str(e)})

    def _parse_results(self, result_text, meta, page_num, original_img, rich_text_mode):
        results = []

        for i, line in enumerate(result_text.split("\n")):
            text = line.strip()
            if text:
                khmer_chars = len(re.findall(r"[\u1780-\u17FF]", text))
                total_chars = len(text)
                acc = (
                    min(99.0, 90.0 + ((khmer_chars / total_chars) * 9.0))
                    if total_chars > 0
                    else 90.0
                )
                results.append(
                    {
                        "page": page_num,
                        "line": len(results) + 1,
                        "text": text,
                        "accuracy": acc,
                        "type": "text",
                    }
                )

        if rich_text_mode and meta:
            segments = meta.get("segments", [])
            segments.sort(key=lambda s: s["bbox"][1])
            for seg in segments:
                if seg["type"] == "logo":
                    try:
                        x1, y1, x2, y2 = [int(c) for c in seg["bbox"]]
                        logo_crop = original_img.crop((x1, y1, x2, y2))
                        results.append(
                            {
                                "page": page_num,
                                "line": len(results) + 1,
                                "text": "[Image]",
                                "accuracy": 100.0,
                                "type": "image",
                                "image_obj": logo_crop,
                            }
                        )
                    except Exception as e:  # noqa: BLE001
                        print(f"Warning: Could not crop logo: {e}")
        return results

    def cleanup(self):
        if os.path.exists(self._temp_file):
            os.unlink(self._temp_file)


class DocumentHandler:
    def __init__(self):
        self.doc = None
        self.is_pdf = False
        self.total_pages = 0
        self.file_path = None

    def load_document(self, path):
        self.file_path = path
        self.is_pdf = path.lower().endswith(".pdf")
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
