#!/usr/bin/env python3
"""Process real crossword images from input/ through the improved pipeline."""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.image_processor import process_image
from app.pdf_generator import generate_pdf

INPUT_DIR = os.path.join(os.path.dirname(__file__), "input")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    images = sorted(glob.glob(os.path.join(INPUT_DIR, "*")))
    images = [f for f in images if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]

    if not images:
        print("No images found in input/")
        return

    processed = []
    for img_path in images:
        name = os.path.splitext(os.path.basename(img_path))[0]
        out_path = os.path.join(OUTPUT_DIR, f"{name}_kindle.png")
        print(f"Processing: {os.path.basename(img_path)} ...")

        options = {
            "auto_perspective": True,
            "threshold_mode": "adaptive",
            "contrast_clip_limit": 1.2,
            "sharpness": 1.3,
            "repair_lines": False,  # Disabled — can thicken noise on photos
            "kindle_model": "scribe",
        }

        try:
            meta = process_image(img_path, out_path, options)
            print(f"  -> {out_path}")
            print(f"     Original: {meta.get('original_size')}")
            print(f"     Output:   {meta.get('processed_size')}")
            print(f"     Perspective corrected: {meta.get('perspective_corrected')}")
            print(f"     Rotation: {meta.get('rotation_angle')}°")
            processed.append(out_path)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    if processed:
        pdf_path = os.path.join(OUTPUT_DIR, "processed_for_kindle.pdf")
        generate_pdf(processed, pdf_path)
        print(f"\nCombined PDF: {pdf_path}")
        print(f"Processed {len(processed)}/{len(images)} images")


if __name__ == "__main__":
    main()
