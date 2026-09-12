"""
Core processing modules for document handling and background OCR execution.
"""

from .document_handler import DocumentHandler
from .ocr_worker import OCRWorker

__all__ = ["DocumentHandler", "OCRWorker"]
