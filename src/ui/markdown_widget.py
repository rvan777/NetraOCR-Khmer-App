import re

import customtkinter as ctk
from PIL import Image, ImageTk


class MarkdownText(ctk.CTkTextbox):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        tb = self._textbox
        tb.configure(wrap="word")

        tb.tag_config("h1", font=("Helvetica", 24, "bold"), spacing1=10, spacing3=5)
        tb.tag_config("h2", font=("Helvetica", 20, "bold"), spacing1=8, spacing3=4)
        tb.tag_config("h3", font=("Helvetica", 16, "bold"), spacing1=6, spacing3=3)
        tb.tag_config("bold", font=("Helvetica", 14, "bold"))
        tb.tag_config("italic", font=("Helvetica", 14, "italic"))
        tb.tag_config("list", lmargin1=20, lmargin2=40)

        self._images = []

    def set_plain_text(self, text):
        tb = self._textbox
        tb.configure(state="normal")
        tb.delete("1.0", "end")
        tb.insert("1.0", text)
        tb.configure(state="disabled")

    def append_page(self, page_num, results, is_rich):
        tb = self._textbox
        tb.configure(state="normal")

        if is_rich:
            tb.insert("end", f"\nPage {page_num}\n", "h2")
            tb.insert("end", "-" * 40 + "\n")
            for item in results:
                if item["type"] == "text":
                    self._insert_rich_text(item["text"] + "\n")
                elif item["type"] == "image" and "image_obj" in item:
                    self._insert_image(item["image_obj"])
        else:
            tb.insert("end", f"\n--- Page {page_num} ---\n")
            for item in results:
                if item["type"] == "text":
                    tb.insert("end", item["text"] + "\n")

        tb.configure(state="disabled")
        tb.see("end")

    def _insert_rich_text(self, text):
        tb = self._textbox
        parts = re.split(r"(\*\*.*?\*\*|\*.*?\*)", text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                tb.insert("end", part[2:-2], "bold")
            elif (
                part.startswith("*")
                and part.endswith("*")
                and not part.startswith("**")
            ):
                tb.insert("end", part[1:-1], "italic")
            else:
                tb.insert("end", part)

    def _insert_image(self, pil_img):
        tb = self._textbox
        try:
            max_w = 350
            if pil_img.width > max_w:
                ratio = max_w / pil_img.width
                pil_img = pil_img.resize(
                    (max_w, int(pil_img.height * ratio)), Image.Resampling.BILINEAR
                )

            tk_img = ImageTk.PhotoImage(pil_img)
            self._images.append(tk_img)
            tb.insert("end", "\n")
            tb.image_create("end", image=tk_img)
            tb.insert("end", "\n")
        except Exception as e:  # noqa: BLE001
            tb.insert("end", f"[Image Error: {e}]\n")
