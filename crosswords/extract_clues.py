#!/usr/bin/env python3
"""
Crossword Clue Extractor
========================
Extracts clue text from a crossword photo using OCR (Tesseract).
Works with the grid contour from extract_grid.py to isolate the
text regions around the grid.

Usage:
    python3 extract_clues.py photos/<image> [--debug]

Output is written to output/<stem>.clues.json and output/<stem>.clues.txt.

Dependencies:
    pip install opencv-python-headless numpy pytesseract Pillow
    apt install tesseract-ocr
"""

import argparse
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np
import pytesseract


def load_image(image_path: str) -> tuple[np.ndarray, np.ndarray]:
    """Load image and grayscale version."""
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img, gray


def find_grid_bbox(gray: np.ndarray) -> tuple[int, int, int, int]:
    """Find the bounding box of the crossword grid."""
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10
    )
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for cnt in contours[:10]:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect = w / h if h > 0 else 0
            area_ratio = cv2.contourArea(approx) / (gray.shape[0] * gray.shape[1])
            if 0.5 < aspect < 2.0 and area_ratio > 0.05:
                return x, y, w, h

    # Fallback: assume grid is roughly center-left
    h, w = gray.shape
    return int(w * 0.05), int(h * 0.05), int(w * 0.5), int(h * 0.5)


def detect_orientation(gray: np.ndarray) -> int:
    """Detect if image is rotated. Returns rotation angle (0, 90, 180, 270)."""
    # Use tesseract's OSD (orientation and script detection)
    try:
        osd = pytesseract.image_to_osd(gray, output_type=pytesseract.Output.DICT)
        return osd.get("rotate", 0)
    except Exception:
        return 0


def rotate_image(img: np.ndarray, angle: int) -> np.ndarray:
    """Rotate image by the given angle (must be 0, 90, 180, or 270)."""
    if angle == 90:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif angle == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    elif angle == 270:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img


def preprocess_for_ocr(gray_region: np.ndarray) -> np.ndarray:
    """Enhance a grayscale region for better OCR."""
    # Upscale small regions
    h, w = gray_region.shape
    if max(h, w) < 1000:
        scale = 2000 / max(h, w)
        gray_region = cv2.resize(gray_region, None, fx=scale, fy=scale,
                                 interpolation=cv2.INTER_CUBIC)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray_region, h=10)

    # Adaptive threshold for clean black-on-white
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 15
    )

    return binary


def find_column_split(gray_region: np.ndarray) -> int | None:
    """Find vertical column divider in a text region by looking for a
    vertical strip with minimal ink (lots of white space)."""
    h, w = gray_region.shape
    if w < 200:
        return None

    # Binarize
    _, binary = cv2.threshold(gray_region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Sum white pixels per column (higher = more white space = potential divider)
    col_whiteness = np.sum(binary == 255, axis=0).astype(float)

    # Only search the middle 60% of the width
    search_start = int(w * 0.2)
    search_end = int(w * 0.8)

    # Smooth to avoid noise
    kernel_size = max(w // 50, 5)
    if kernel_size % 2 == 0:
        kernel_size += 1
    smoothed = cv2.GaussianBlur(col_whiteness.reshape(1, -1), (1, kernel_size), 0)[0]

    # Find the column with most whitespace in the search range
    search_region = smoothed[search_start:search_end]
    if len(search_region) == 0:
        return None

    best_col = search_start + int(np.argmax(search_region))

    # Verify it's actually a significant gap (at least 80% white)
    if col_whiteness[best_col] > h * 0.8:
        return best_col

    return None


def extract_text_regions(img: np.ndarray, gray: np.ndarray,
                         grid_bbox: tuple[int, int, int, int],
                         debug: bool = False) -> dict[str, np.ndarray]:
    """Extract text regions around the grid, splitting multi-column layouts."""
    gx, gy, gw, gh = grid_bbox
    ih, iw = gray.shape
    margin = 10

    regions = {}

    # Below the grid (most common location for clues)
    below_y = min(gy + gh + margin, ih)
    if below_y < ih - 50:
        below_region = gray[below_y:ih, 0:iw]
        # Try to detect and split columns
        split_x = find_column_split(below_region)
        if split_x is not None:
            regions["below_left"] = below_region[:, :split_x]
            right_half = below_region[:, split_x:]
            # The right half often has: solved grid + DOWN clues in sub-columns
            # Try to split it further
            split_x2 = find_column_split(right_half)
            if split_x2 is not None:
                regions["below_mid"] = right_half[:, :split_x2]
                regions["below_right"] = right_half[:, split_x2:]
            else:
                regions["below_right"] = right_half
        else:
            regions["below"] = below_region

    # Right of the grid
    right_x = min(gx + gw + margin, iw)
    if right_x < iw - 50:
        regions["right"] = gray[0:ih, right_x:iw]

    # Left of the grid (for close-up photos where clues are on the left)
    left_x = max(gx - margin, 0)
    if left_x > 50:
        regions["left"] = gray[0:ih, 0:left_x]

    # Above the grid (for title/author info)
    above_y = max(gy - margin, 0)
    if above_y > 50:
        regions["above"] = gray[0:above_y, 0:iw]

    return regions


def ocr_region(gray_region: np.ndarray, label: str = "") -> str:
    """Run OCR on a preprocessed region."""
    if gray_region is None or gray_region.size == 0:
        return ""

    processed = preprocess_for_ocr(gray_region)

    # PSM 6 = Assume a single uniform block of text
    # PSM 4 = Assume a single column of text of variable sizes
    config = "--psm 4 --oem 3"
    text = pytesseract.image_to_string(processed, config=config)
    return text.strip()


def parse_clues(raw_text: str, default_section: str = None) -> dict:
    """Parse raw OCR text into structured across/down clue dictionaries.

    Args:
        raw_text: Raw OCR text
        default_section: If set, use this as the initial section ("across" or "down")
    """
    lines = raw_text.split("\n")
    across = {}
    down = {}
    current_section = default_section
    current_num = None
    current_text = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect section headers
        upper = line.upper()
        if re.match(r'^ACROSS\b', upper):
            if current_num and current_text:
                _store_clue(current_section, current_num, current_text, across, down)
            current_section = "across"
            current_num = None
            current_text = ""
            continue
        if re.match(r'^DOWN\b', upper):
            if current_num and current_text:
                _store_clue(current_section, current_num, current_text, across, down)
            current_section = "down"
            current_num = None
            current_text = ""
            continue

        # Try to match a numbered clue line: "23 Some clue text"
        # or "23. Some clue text"
        m = re.match(r'^(\d{1,3})[.\s)\-]+(.+)', line)
        if m:
            # Save previous clue
            if current_num and current_text:
                _store_clue(current_section, current_num, current_text, across, down)

            current_num = int(m.group(1))
            current_text = m.group(2).strip()

            # Auto-detect section from clue number ordering
            if current_section is None:
                current_section = "across"
        else:
            # Continuation line — only append if it looks like real text
            # (skip lines that are mostly garbage characters from OCR artifacts)
            if current_num and _is_plausible_text(line):
                current_text += " " + line

    # Don't forget the last clue
    if current_num and current_text:
        _store_clue(current_section, current_num, current_text, across, down)

    return {"across": across, "down": down}


def _is_plausible_text(text: str) -> bool:
    """Check if a line looks like real English text vs OCR garbage."""
    if not text:
        return False
    # Count letter/space chars vs total
    alpha_count = sum(1 for c in text if c.isalpha() or c in ' ,.\'"!?;:-_()/')
    ratio = alpha_count / len(text) if text else 0
    return ratio > 0.6 and len(text) > 1


def _store_clue(section, num, text, across, down):
    """Store a clue in the appropriate dictionary."""
    text = re.sub(r'\s+', ' ', text).strip()
    if section == "across":
        across[str(num)] = text
    elif section == "down":
        down[str(num)] = text


def merge_clue_dicts(all_clues: list[dict]) -> dict:
    """Merge clues extracted from multiple regions."""
    merged_across = {}
    merged_down = {}

    for clues in all_clues:
        for num, text in clues.get("across", {}).items():
            if num not in merged_across or len(text) > len(merged_across[num]):
                merged_across[num] = text
        for num, text in clues.get("down", {}).items():
            if num not in merged_down or len(text) > len(merged_down[num]):
                merged_down[num] = text

    return {"across": merged_across, "down": merged_down}


def format_clues_text(clues: dict, metadata: dict = None) -> str:
    """Format clues as readable text."""
    lines = []

    if metadata:
        lines.append("=" * 60)
        if "title" in metadata:
            lines.append(metadata["title"])
        if "date" in metadata:
            lines.append(f"Date: {metadata['date']}")
        if "author" in metadata:
            lines.append(f"By: {metadata['author']}")
        lines.append("=" * 60)
        lines.append("")

    lines.append("ACROSS")
    lines.append("-" * 40)
    for num in sorted(clues["across"].keys(), key=lambda x: int(x)):
        lines.append(f"{num:>3}. {clues['across'][num]}")

    lines.append("")
    lines.append("DOWN")
    lines.append("-" * 40)
    for num in sorted(clues["down"].keys(), key=lambda x: int(x)):
        lines.append(f"{num:>3}. {clues['down'][num]}")

    return "\n".join(lines)


def extract_clues(image_path: str, debug: bool = False) -> dict:
    """Main clue extraction pipeline."""
    print(f"Loading image: {image_path}")
    img, gray = load_image(image_path)

    # Check orientation
    print("Detecting orientation...")
    rotation = detect_orientation(gray)
    if rotation != 0:
        print(f"  Rotating by {rotation}°")
        img = rotate_image(img, rotation)
        gray = rotate_image(gray, rotation)
    else:
        print("  Image is upright")

    # Find the grid to know where the clue text regions are
    print("Finding grid boundary...")
    grid_bbox = find_grid_bbox(gray)
    gx, gy, gw, gh = grid_bbox
    print(f"  Grid at: x={gx}, y={gy}, w={gw}, h={gh}")

    # Extract text regions around the grid
    print("Extracting text regions...")
    regions = extract_text_regions(img, gray, grid_bbox, debug)
    print(f"  Found {len(regions)} text regions: {list(regions.keys())}")

    # OCR each region
    all_clues = []
    raw_texts = {}
    for label, region in regions.items():
        print(f"  OCR on '{label}' region ({region.shape[1]}x{region.shape[0]})...")
        text = ocr_region(region, label)
        raw_texts[label] = text
        if text:
            # Hint the parser about expected section based on column position
            # Left column typically has ACROSS, right/mid has DOWN
            default_section = None
            if "left" in label:
                default_section = "across"
            elif label in ("below_right", "below_mid"):
                default_section = "down"
            clues = parse_clues(text, default_section=default_section)
            n_across = len(clues["across"])
            n_down = len(clues["down"])
            print(f"    Found {n_across} across + {n_down} down clues")
            all_clues.append(clues)

    # Merge clues from all regions
    merged = merge_clue_dicts(all_clues)
    total = len(merged["across"]) + len(merged["down"])
    print(f"\nTotal extracted: {len(merged['across'])} across + {len(merged['down'])} down = {total} clues")

    # Save debug info
    if debug:
        output_dir = Path(image_path).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        stem = Path(image_path).stem

        # Save annotated image showing regions
        debug_img = img.copy()
        colors = {"above": (0, 255, 255), "below": (0, 255, 0),
                  "left": (255, 0, 0), "right": (255, 0, 255)}
        cv2.rectangle(debug_img, (gx, gy), (gx + gw, gy + gh), (0, 0, 255), 3)
        debug_path = str(output_dir / f"{stem}.clue_regions.png")
        cv2.imwrite(debug_path, debug_img)
        print(f"\nDebug image saved: {debug_path}")

        # Save raw OCR text
        raw_path = str(output_dir / f"{stem}.ocr_raw.txt")
        with open(raw_path, "w") as f:
            for label, text in raw_texts.items():
                f.write(f"=== {label.upper()} REGION ===\n")
                f.write(text + "\n\n")
        print(f"Raw OCR saved: {raw_path}")

    return {
        "source": image_path,
        "clues": merged,
        "raw_text": raw_texts,
    }


def main():
    parser = argparse.ArgumentParser(description="Extract crossword clues via OCR")
    parser.add_argument("image", help="Path to the crossword image")
    parser.add_argument("--debug", "-d", action="store_true", help="Save debug outputs")
    parser.add_argument("--output", "-o", help="Output JSON path")
    args = parser.parse_args()

    result = extract_clues(args.image, debug=args.debug)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        stem = Path(args.image).stem
        output_dir = Path(args.image).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{stem}.clues.json")

    # Save JSON
    save_data = {
        "source": result["source"],
        "clues": result["clues"],
    }
    with open(output_path, "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"\nClues saved to: {output_path}")

    # Save text version
    txt_path = str(Path(output_path).with_suffix(".txt"))
    formatted = format_clues_text(result["clues"])
    with open(txt_path, "w") as f:
        f.write(formatted + "\n")
    print(f"Text clues saved to: {txt_path}")


if __name__ == "__main__":
    main()
