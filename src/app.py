import queue
import threading
from tkinter import Menu, filedialog, messagebox

import customtkinter as ctk

from core.document_handler import DocumentHandler
from core.ocr_worker import OCRWorker
from ui.markdown_widget import MarkdownText
from utils.exporter import export_results

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class KhmerOCRApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Netra Khmer OCR Desktop")
        self.geometry("1100x750")
        self.minsize(950, 700)

        self.doc_handler = DocumentHandler()
        self.result_queue = queue.Queue()
        self.worker = None
        self.is_processing = False
        self.all_results = []

        # Settings
        self.show_line_numbers = ctk.BooleanVar(value=False)
        self.show_accuracy = ctk.BooleanVar(value=False)
        self.rich_text_mode = ctk.BooleanVar(value=False)
        self.ocr_mode = ctk.StringVar(value="Fast (Blockwise)")

        # Strictly following Netra-OCR CLI documentation:
        # - decoder="blockwise" is fastest, beam_width is ignored.
        # - decoder="ar" with beam_width=1 is greedy (standard).
        # - Higher beam_width improves accuracy at the cost of speed.
        # - conf (YOLO confidence) remains at default 0.25 to avoid detecting noise.
        self.ocr_modes = {
            "Fast (Blockwise)": {"decoder": "blockwise", "beam_width": 1, "conf": 0.25},
            "Standard (Greedy)": {"decoder": "ar", "beam_width": 1, "conf": 0.25},
            "Beam Search": {"decoder": "ar", "beam_width": 3, "conf": 0.25},
            "High Accuracy": {"decoder": "ar", "beam_width": 5, "conf": 0.25}
        }

        self.setup_menu()
        self.setup_ui()

    def setup_menu(self):
        self.menu_bar = Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open File...", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        help_menu = Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left: Preview
        self.preview_frame = ctk.CTkFrame(self.main_frame, width=450)
        self.preview_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="No Document Loaded", font=ctk.CTkFont(size=16))
        self.preview_label.pack(expand=True, fill="both", padx=10, pady=10)

        self.nav_frame = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.prev_btn = ctk.CTkButton(self.nav_frame, text="<", width=40, command=lambda: self.change_page(-1),
                                      state="disabled")
        self.prev_btn.pack(side="left", padx=10)
        self.page_label = ctk.CTkLabel(self.nav_frame, text="Page 0 / 0", font=ctk.CTkFont(size=14))
        self.page_label.pack(side="left", expand=True)
        self.next_btn = ctk.CTkButton(self.nav_frame, text=">", width=40, command=lambda: self.change_page(1),
                                      state="disabled")
        self.next_btn.pack(side="right", padx=10)

        # Right: Results
        self.result_frame = ctk.CTkFrame(self.main_frame, width=600)
        self.result_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=5)
        ctk.CTkLabel(self.result_frame, text="Extracted Document", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=10, pady=(10, 0))

        self.markdown_text = MarkdownText(self.result_frame)
        self.markdown_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.markdown_text.set_plain_text(
            "Welcome!\n\n1. Open a PDF or Image.\n2. Click 'Process OCR'.\n3. Check 'Settings' to enable Rich Text.")

        # Bottom Bar
        self.bottom_frame = ctk.CTkFrame(self, height=70)
        self.bottom_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(self.bottom_frame, text="Open File", font=ctk.CTkFont(size=14), command=self.open_file).pack(
            side="left", padx=10, pady=10)
        self.process_btn = ctk.CTkButton(self.bottom_frame, text="Process OCR", font=ctk.CTkFont(size=14),
                                         state="disabled", command=self.start_ocr)
        self.process_btn.pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(self.bottom_frame, text="Mode:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(20, 5),
                                                                                      pady=10)
        # Change the values list to dynamically use the dictionary keys
        self.ocr_mode_menu = ctk.CTkOptionMenu(
            self.bottom_frame, variable=self.ocr_mode,
            values=list(self.ocr_modes.keys()),
            width=180, font=ctk.CTkFont(size=14)
        )
        self.ocr_mode_menu.pack(side="left", padx=5, pady=10)

        ctk.CTkButton(self.bottom_frame, text="Settings", width=100, command=self.open_settings).pack(side="left",
                                                                                                      padx=20, pady=10)

        self.export_var = ctk.StringVar(value="Export As...")
        self.export_menu = ctk.CTkOptionMenu(self.bottom_frame, variable=self.export_var,
                                             values=["Export as .txt", "Export as .md", "Export as .docx",
                                                     "Export as .xlsx"], command=self.handle_export, state="disabled",
                                             font=ctk.CTkFont(size=14))
        self.export_menu.pack(side="right", padx=10, pady=10)

        self.progress_bar = ctk.CTkProgressBar(self.bottom_frame, width=200)
        self.progress_bar.pack(side="right", padx=10, pady=10)
        self.progress_bar.set(0)

    def show_user_guide(self):
        guide = ctk.CTkToplevel(self)
        guide.title("User Guide")
        guide.geometry("700x600")
        guide.transient(self)
        guide_md = MarkdownText(guide)
        guide_md.pack(fill="both", expand=True, padx=10, pady=10)
        guide_md.set_plain_text(
            "Netra Khmer OCR - User Guide\n\n1. Open File: Load a scanned PDF or image.\n2. Process OCR: Choose a mode and extract text.\n3. Settings: Toggle Rich Text, Line Numbers, or Accuracy.\n4. Export: Save as TXT, MD, DOCX (with images), or XLSX.")

    def show_about(self):
        messagebox.showinfo("About",
                            "Netra Khmer OCR Desktop v0.1-alpha\n\nPowered by Netra-OCR Engine\nOptimized Multi-Threaded Architecture\n\n© 2026 Qwen Studio - AI Lab")

    def open_settings(self):
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Display Settings")
        settings_window.geometry("350x240")
        settings_window.resizable(False, False)
        settings_window.transient(self)
        settings_window.grab_set()

        ctk.CTkLabel(settings_window, text="Display & Export Settings", font=ctk.CTkFont(weight="bold", size=16)).pack(
            pady=10)
        ctk.CTkCheckBox(settings_window, text="Enable Rich Text (Images, Bold)", variable=self.rich_text_mode).pack(
            anchor="w", padx=20, pady=5)
        ctk.CTkCheckBox(settings_window, text="Show Line Numbers", variable=self.show_line_numbers).pack(anchor="w",
                                                                                                         padx=20,
                                                                                                         pady=5)
        ctk.CTkCheckBox(settings_window, text="Show Accuracy Percentage", variable=self.show_accuracy).pack(anchor="w",
                                                                                                            padx=20,
                                                                                                            pady=5)
        ctk.CTkLabel(settings_window, text="*Rich text is slower but includes images", font=ctk.CTkFont(size=10),
                     text_color="gray").pack(pady=5)
        ctk.CTkButton(settings_window, text="Close", width=80, command=settings_window.destroy).pack(pady=5)

    def open_file(self):
        filetypes = [("Document Files", "*.pdf *.png *.jpg *.jpeg *.bmp *.tiff")]
        path = filedialog.askopenfilename(title="Select Document", filetypes=filetypes)
        if not path: return

        self.doc_handler.load_document(path)
        self.process_btn.configure(state="normal")
        self.export_menu.configure(state="disabled")
        self.all_results = []
        self.markdown_text.set_plain_text("Document loaded.\nClick 'Process OCR' to begin.")
        self.current_page = 0

        if self.doc_handler.is_pdf:
            self.render_preview(self.current_page)
        else:
            self.page_label.configure(text="Image Preview")
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")
            img = self.doc_handler.get_preview_image(0)
            self.ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            self.preview_label.configure(image=self.ctk_image, text="")

    def change_page(self, direction):
        new_page = self.current_page + direction
        if 0 <= new_page < self.doc_handler.total_pages:
            self.current_page = new_page
            self.render_preview(self.current_page)

    def render_preview(self, page_num):
        img = self.doc_handler.get_preview_image(page_num)

        # Force clear the label first to prevent UI ghosting
        self.preview_label.configure(image="", text="")

        # Create new CTkImage and apply
        self.ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
        self.preview_label.configure(image=self.ctk_image, text="")

        self.page_label.configure(text=f"Page {page_num + 1} / {self.doc_handler.total_pages}")
        self.prev_btn.configure(state="normal" if page_num > 0 else "disabled")
        self.next_btn.configure(state="normal" if page_num < self.doc_handler.total_pages - 1 else "disabled")

    # =====================================================================
    # THREADED OCR PROCESSING
    # =====================================================================
    def start_ocr(self):
        self.process_btn.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)
        self.all_results = []
        self.markdown_text.set_plain_text("Starting background thread...")
        self.is_processing = True

        # Initialize worker and start thread
        self.worker = OCRWorker(self.doc_handler, self.result_queue)
        threading.Thread(target=self.worker.process,
                         args=(self.ocr_modes[self.ocr_mode.get()], self.rich_text_mode.get()), daemon=True).start()

        # Start polling the queue
        self.after(50, self.poll_queue)

    def poll_queue(self):
        try:
            while True:
                msg = self.result_queue.get_nowait()
                if msg["type"] == "progress":
                    self.progress_bar.set(msg["value"])
                elif msg["type"] == "page_done":
                    self.all_results.extend(msg["results"])
                    # Incremental UI update (Prevents UI hang at the end)
                    self.markdown_text.append_page(msg["page"], msg["results"], self.rich_text_mode.get())
                elif msg["type"] == "status":
                    self.markdown_text.set_plain_text(msg["msg"])
                elif msg["type"] == "finished":
                    self._on_finished()
                    return
                elif msg["type"] == "error":
                    self._on_error(msg["msg"])
                    return
        except queue.Empty:
            pass

        if self.is_processing:
            self.after(50, self.poll_queue)

    def _on_finished(self):
        self.is_processing = False
        self.progress_bar.set(1.0)
        self.export_menu.configure(state="normal")
        self.process_btn.configure(state="normal", text="Process OCR")
        messagebox.showinfo("Success", f"OCR Processing Complete!\nMode: {self.ocr_mode.get()}")
        if self.worker: self.worker.cleanup()

    def _on_error(self, error_msg):
        self.is_processing = False
        self.process_btn.configure(state="normal", text="Process OCR")
        self.progress_bar.set(0)
        messagebox.showerror("Error", f"An error occurred:\n{error_msg}")
        if self.worker: self.worker.cleanup()

    def handle_export(self, choice):
        if not self.all_results:
            messagebox.showwarning("Warning", "No data to export.")
            return

        ext_map = {
            "Export as .txt": (".txt", "Text Files"),
            "Export as .md": (".md", "Markdown Files"),
            "Export as .docx": (".docx", "Word Documents"),
            "Export as .xlsx": (".xlsx", "Excel Files")
        }
        ext, ftype = ext_map.get(choice, (".txt", "Text Files"))

        path = filedialog.asksaveasfilename(title="Save Extracted Text", defaultextension=ext,
                                            filetypes=[(ftype, f"*{ext}")])
        if not path: return

        success, result = export_results(
            choice, self.all_results,
            self.show_line_numbers.get(),
            self.show_accuracy.get(),
            path
        )

        if success:
            messagebox.showinfo("Success", f"File saved to:\n{result}")
        else:
            messagebox.showerror("Export Error", f"Failed to save file:\n{result}")


if __name__ == "__main__":
    app = KhmerOCRApp()
    app.mainloop()