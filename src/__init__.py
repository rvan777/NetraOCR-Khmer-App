"""
Netra Khmer OCR Desktop Application

This package contains the main desktop application built with CustomTkinter,
powered by the Netra-OCR engine for offline Khmer text recognition.
"""

# Expose the main app class at the package level
# This allows: from src import KhmerOCRApp
from .app import KhmerOCRApp

__version__ = "1.0.0"
__all__ = ["KhmerOCRApp"]
