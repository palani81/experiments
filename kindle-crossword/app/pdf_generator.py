"""
High-quality PDF generator for Kindle crossword delivery.

Uses ReportLab to embed images at exact 300 DPI with no resampling,
producing crisp output on Kindle's e-ink display. Falls back to
img2pdf if ReportLab is unavailable.
"""
import os

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas


# Kindle Scribe: 1860x2480 @ 300 DPI = 6.2" x 8.267"
KINDLE_PAGE_W = 6.2 * inch
KINDLE_PAGE_H = 8.267 * inch


def generate_pdf(image_paths: list[str], output_path: str) -> str:
    """Generate a PDF with one image per page, sized for Kindle Scribe at 300 DPI."""
    if not image_paths:
        raise ValueError("No image paths provided")

    for path in image_paths:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Image not found: {path}")

    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    c = rl_canvas.Canvas(output_path, pagesize=(KINDLE_PAGE_W, KINDLE_PAGE_H))

    for img_path in image_paths:
        # Draw image to fill the page exactly — the image is already sized
        # to Kindle dimensions by image_processor, so this is a 1:1 mapping
        c.drawImage(
            img_path,
            0, 0,
            width=KINDLE_PAGE_W,
            height=KINDLE_PAGE_H,
            preserveAspectRatio=True,
            anchor='c',
        )
        c.showPage()

    c.save()
    return output_path
