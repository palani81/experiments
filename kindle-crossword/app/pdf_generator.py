import os

import img2pdf


def generate_pdf(image_paths: list[str], output_path: str) -> str:
    if not image_paths:
        raise ValueError("No image paths provided")

    for path in image_paths:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Image not found: {path}")

    # Kindle Scribe: 1860x2480 at 300 DPI = 6.2" x 8.27"
    # Set explicit page size so images fill the screen correctly
    page_w = img2pdf.mm_to_pt(157.48)  # 6.2 inches
    page_h = img2pdf.mm_to_pt(210.06)  # 8.27 inches
    layout = img2pdf.get_layout_fun(pagesize=(page_w, page_h), fit=img2pdf.FitMode.into)

    pdf_bytes = img2pdf.convert(image_paths, layout_fun=layout)

    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    return output_path
