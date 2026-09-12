import os
import re
import tempfile

from netra_ocr.ocr_engine import KhmerOCRPipeline

# Check for custom model directory set by installer
CUSTOM_MODEL_DIR = os.environ.get("NETRA_OCR_MODEL_DIR")
if CUSTOM_MODEL_DIR:
    # Point HuggingFace cache to our local directory
    os.environ["HF_HOME"] = CUSTOM_MODEL_DIR


class OCRWorker:
    def __init__(self, doc_handler, result_queue):
        self.doc_handler = doc_handler
        self.result_queue = result_queue
        self.pipeline = None
        self.current_decoder = None

        # PERFORMANCE FIX: Create ONE temp file and reuse it for all pages
        self._temp_file = tempfile.NamedTemporaryFile(
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
                # Send progress update to UI
                self.result_queue.put(
                    {"type": "progress", "value": (page_num + 1) / total_pages}
                )

                # Get image in memory
                img = self.doc_handler.get_page_image(page_num, dpi=150)

                # Overwrite the single temp file (much faster than creating new ones)
                img.save(self._temp_file, format="PNG")

                # Run OCR
                return_segments = rich_text_mode
                ocr_result = self.pipeline.process_image(
                    self._temp_file,
                    output_path=None,
                    beam_width=mode_config["beam_width"],
                    batch_size=16,
                    return_segments=return_segments,
                )

                # ✅ FIX: Handle the return value based on the return_segments flag
                if return_segments:
                    result_text, meta = ocr_result
                else:
                    result_text = ocr_result
                    meta = None

                # Parse results and send to UI
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

        # 1. Process Text
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

        # 2. Process Images (IN-MEMORY CROPPING) - Only if meta exists
        if rich_text_mode and meta:
            segments = meta.get("segments", [])
            segments.sort(key=lambda s: s["bbox"][1])
            for seg in segments:
                if seg["type"] == "logo":
                    try:
                        x1, y1, x2, y2 = [int(c) for c in seg["bbox"]]
                        # Crop directly from the original_img in memory! No disk I/O!
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
