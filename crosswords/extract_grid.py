#!/usr/bin/env python3
"""
Crossword Grid Extractor
========================
Extracts the empty grid structure (black/white cells and clue numbers)
from a photograph of a newspaper crossword puzzle.

Usage:
    python3 extract_grid.py photos/<image> [--output <output_path>] [--debug]

Output files are written to the output/ directory by default.

Dependencies:
    pip install opencv-python-headless numpy Pillow
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np


def load_and_preprocess(image_path: str) -> tuple[np.ndarray, np.ndarray]:
    """Load image and create a clean grayscale version."""
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img, gray


def find_grid_contour(gray: np.ndarray) -> np.ndarray | None:
    """Find the largest square-ish contour (the crossword grid)."""
    # Adaptive threshold to handle uneven lighting in photos
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10
    )
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Sort by area, largest first
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for cnt in contours[:10]:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            # Check if roughly square (aspect ratio near 1)
            x, y, w, h = cv2.boundingRect(approx)
            aspect = w / h if h > 0 else 0
            if 0.7 < aspect < 1.4 and w > gray.shape[1] * 0.3:
                return approx
    return None


def order_points(pts: np.ndarray) -> np.ndarray:
    """Order 4 points as: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]
    rect[3] = pts[np.argmax(d)]
    return rect


def perspective_transform(img: np.ndarray, contour: np.ndarray, size: int = 750) -> np.ndarray:
    """Warp the grid region to a square image."""
    pts = contour.reshape(4, 2).astype("float32")
    ordered = order_points(pts)
    dst = np.array([[0, 0], [size, 0], [size, size], [0, size]], dtype="float32")
    M = cv2.getPerspectiveTransform(ordered, dst)
    return cv2.warpPerspective(img, M, (size, size))


def detect_grid_size(warped_gray: np.ndarray) -> int:
    """Detect grid dimensions (e.g., 15 for a 15x15 grid) using line detection."""
    size = warped_gray.shape[0]

    # Use edge detection and Hough lines
    edges = cv2.Canny(warped_gray, 50, 150)

    # Project onto axes to find grid lines
    h_proj = np.sum(edges, axis=1).astype(float)
    v_proj = np.sum(edges, axis=0).astype(float)

    # Smooth and find peaks
    kernel = np.ones(3) / 3
    h_proj = np.convolve(h_proj, kernel, mode='same')
    v_proj = np.convolve(v_proj, kernel, mode='same')

    # Find peaks (grid lines)
    h_threshold = np.mean(h_proj) + np.std(h_proj)
    v_threshold = np.mean(v_proj) + np.std(v_proj)

    h_lines = find_line_positions(h_proj, h_threshold, min_distance=size // 25)
    v_lines = find_line_positions(v_proj, v_threshold, min_distance=size // 25)

    # Grid size = number of gaps between lines
    n_rows = max(len(h_lines) - 1, 1)
    n_cols = max(len(v_lines) - 1, 1)

    # Typically crosswords are square; pick the most common standard size
    avg = (n_rows + n_cols) / 2
    for standard in [15, 14, 13, 17, 21]:
        if abs(avg - standard) <= 2:
            return standard

    return round(avg)


def find_line_positions(projection: np.ndarray, threshold: float, min_distance: int) -> list[int]:
    """Find positions of grid lines from a projection profile."""
    above = projection > threshold
    positions = []
    i = 0
    while i < len(above):
        if above[i]:
            # Find center of this peak
            start = i
            while i < len(above) and above[i]:
                i += 1
            center = (start + i) // 2
            if not positions or center - positions[-1] >= min_distance:
                positions.append(center)
        else:
            i += 1
    return positions


def classify_cells(
    warped_gray: np.ndarray,
    grid_size: int,
) -> list[list[str]]:
    """
    Classify each cell as black (#) or white (.).
    Returns a grid_size x grid_size matrix.
    """
    h, w = warped_gray.shape
    cell_h = h / grid_size
    cell_w = w / grid_size

    # Margins to avoid grid lines
    margin_ratio = 0.15
    grid = []

    for r in range(grid_size):
        row = []
        for c in range(grid_size):
            y1 = int(r * cell_h + cell_h * margin_ratio)
            y2 = int((r + 1) * cell_h - cell_h * margin_ratio)
            x1 = int(c * cell_w + cell_w * margin_ratio)
            x2 = int((c + 1) * cell_w - cell_w * margin_ratio)

            cell = warped_gray[y1:y2, x1:x2]
            mean_val = np.mean(cell)

            if mean_val < 100:
                row.append("#")
            else:
                row.append(".")
        grid.append(row)

    return grid


def draw_debug_overlay(
    warped: np.ndarray,
    grid: list[list[str]],
    numbers: dict[tuple[int, int], int],
    grid_size: int,
) -> np.ndarray:
    """Draw debug overlay showing the FINAL grid classification and numbering."""
    h, w = warped.shape[:2]
    cell_h = h / grid_size
    cell_w = w / grid_size

    # Start with a lightened copy so overlays are visible
    debug_img = cv2.addWeighted(warped, 0.5, np.full_like(warped, 255), 0.5, 0)

    for r in range(grid_size):
        for c in range(grid_size):
            x1 = int(c * cell_w)
            y1 = int(r * cell_h)
            x2 = int((c + 1) * cell_w)
            y2 = int((r + 1) * cell_h)

            if grid[r][c] == "#":
                # Solid black fill for detected black cells
                cv2.rectangle(debug_img, (x1 + 1, y1 + 1), (x2 - 1, y2 - 1), (30, 30, 30), -1)
                cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            else:
                # Thin green border for white cells
                cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 180, 0), 1)

            # Draw clue number if present
            if (r, c) in numbers:
                num = numbers[(r, c)]
                cv2.putText(
                    debug_img, str(num),
                    (x1 + 3, y1 + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 0, 0), 1,
                )

    return debug_img


def detect_numbers_in_cells(
    warped_gray: np.ndarray,
    grid_size: int,
    grid: list[list[str]],
) -> dict[tuple[int, int], int]:
    """
    Detect clue numbers in white cells by looking for dark pixels in the
    top-left corner of each cell.
    Returns a dict mapping (row, col) -> estimated clue number.
    """
    h, w = warped_gray.shape
    cell_h = h / grid_size
    cell_w = w / grid_size

    numbered_cells = {}
    number_regions = []

    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] == "#":
                continue

            # Look at top-left quadrant of the cell for a number
            y1 = int(r * cell_h + 1)
            y2 = int(r * cell_h + cell_h * 0.4)
            x1 = int(c * cell_w + 1)
            x2 = int(c * cell_w + cell_w * 0.45)

            region = warped_gray[y1:y2, x1:x2]
            # Threshold for dark pixels (the number text)
            _, binary = cv2.threshold(region, 140, 255, cv2.THRESH_BINARY_INV)
            dark_ratio = np.sum(binary > 0) / binary.size if binary.size > 0 else 0

            if dark_ratio > 0.05:  # Has meaningful dark content = likely a number
                numbered_cells[(r, c)] = True
                number_regions.append((r, c, dark_ratio))

    # Assign sequential numbers based on standard crossword numbering
    # (left-to-right, top-to-bottom)
    number_map = {}
    current_number = 1
    for r in range(grid_size):
        for c in range(grid_size):
            if (r, c) in numbered_cells:
                number_map[(r, c)] = current_number
                current_number += 1

    return number_map


def should_be_numbered(grid: list[list[str]], r: int, c: int, size: int) -> bool:
    """Check if a white cell should be numbered per crossword rules."""
    if grid[r][c] == "#":
        return False

    starts_across = False
    starts_down = False

    # Starts across: left edge or black to the left, AND white to the right
    if c == 0 or grid[r][c - 1] == "#":
        if c + 1 < size and grid[r][c + 1] != "#":
            starts_across = True

    # Starts down: top edge or black above, AND white below
    if r == 0 or grid[r - 1][c] == "#":
        if r + 1 < size and grid[r + 1][c] != "#":
            starts_down = True

    return starts_across or starts_down


def assign_numbers(grid: list[list[str]], size: int) -> dict[tuple[int, int], int]:
    """Assign clue numbers based on standard crossword numbering rules."""
    number_map = {}
    current = 1
    for r in range(size):
        for c in range(size):
            if should_be_numbered(grid, r, c, size):
                number_map[(r, c)] = current
                current += 1
    return number_map


def refine_grid_with_ocr_numbers(
    grid: list[list[str]],
    detected_numbers: dict[tuple[int, int], int],
    size: int,
) -> list[list[str]]:
    """
    Use detected number positions to refine the grid.
    If a cell is detected as having a number but classified as black,
    flip it to white. Similarly validate black cells.
    """
    refined = [row[:] for row in grid]
    for (r, c) in detected_numbers:
        if refined[r][c] == "#":
            # Numbered cell can't be black
            refined[r][c] = "."
    return refined


def grid_to_ascii(grid: list[list[str]], numbers: dict[tuple[int, int], int], size: int) -> str:
    """Render the grid as ASCII art."""
    lines = []
    # Header
    col_width = 4
    header = "    " + "".join(f"{c+1:>{col_width}}" for c in range(size))
    lines.append(header)
    lines.append("  ┌" + "┬".join(["───"] * size) + "┐")

    for r in range(size):
        row_str = f"{r+1:>2}│"
        for c in range(size):
            if grid[r][c] == "#":
                row_str += "███│"
            elif (r, c) in numbers:
                n = numbers[(r, c)]
                row_str += f"{n:>3}│"
            else:
                row_str += "   │"
        lines.append(row_str)
        if r < size - 1:
            lines.append("  ├" + "┼".join(["───"] * size) + "┤")

    lines.append("  └" + "┴".join(["───"] * size) + "┘")
    return "\n".join(lines)


def grid_to_json(
    grid: list[list[str]],
    numbers: dict[tuple[int, int], int],
    size: int,
    image_path: str,
) -> dict:
    """Create a JSON-serializable representation of the grid."""
    # Build the grid matrix: 0=black, -1=unnumbered white, N=numbered white
    matrix = []
    for r in range(size):
        row = []
        for c in range(size):
            if grid[r][c] == "#":
                row.append(0)
            elif (r, c) in numbers:
                row.append(numbers[(r, c)])
            else:
                row.append(-1)
        matrix.append(row)

    # Determine across/down word starts
    across_starts = {}
    down_starts = {}
    for (r, c), n in sorted(numbers.items(), key=lambda x: x[1]):
        # Check if starts across
        if c == 0 or grid[r][c - 1] == "#":
            if c + 1 < size and grid[r][c + 1] != "#":
                # Find length
                length = 1
                while c + length < size and grid[r][c + length] != "#":
                    length += 1
                if length >= 2:
                    across_starts[n] = {"row": r, "col": c, "length": length}
        # Check if starts down
        if r == 0 or grid[r - 1][c] == "#":
            if r + 1 < size and grid[r + 1][c] != "#":
                length = 1
                while r + length < size and grid[r + length][c] != "#":
                    length += 1
                if length >= 2:
                    down_starts[n] = {"row": r, "col": c, "length": length}

    return {
        "source": image_path,
        "grid_size": size,
        "black_cells": sum(1 for r in grid for c in r if c == "#"),
        "white_cells": sum(1 for r in grid for c in r if c == "."),
        "numbered_cells": len(numbers),
        "grid": matrix,
        "across_word_starts": {str(k): v for k, v in across_starts.items()},
        "down_word_starts": {str(k): v for k, v in down_starts.items()},
    }


def extract_crossword_grid(image_path: str, debug: bool = False) -> dict:
    """Main extraction pipeline."""
    print(f"Loading image: {image_path}")
    img, gray = load_and_preprocess(image_path)

    # Step 1: Find the grid boundary
    print("Finding grid contour...")
    contour = find_grid_contour(gray)
    if contour is None:
        # Fallback: try to find the grid using the full image with different methods
        print("  No quad contour found. Trying alternative detection...")
        contour = find_grid_fallback(gray)
        if contour is None:
            print("  ERROR: Could not find crossword grid in image.")
            print("  Try cropping the image to just the grid area.")
            sys.exit(1)

    print(f"  Grid contour found at: {contour.reshape(4,2).tolist()}")

    # Step 2: Perspective-correct the grid
    warped_size = 900  # px per side
    warped = perspective_transform(img, contour, warped_size)
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

    # Step 3: Detect grid dimensions
    print("Detecting grid size...")
    grid_size = detect_grid_size(warped_gray)
    print(f"  Detected: {grid_size}x{grid_size}")

    # Step 4: Classify cells (black vs white)
    print("Classifying cells...")
    grid = classify_cells(warped_gray, grid_size)
    black_count = sum(1 for r in grid for c in r if c == "#")
    print(f"  Black cells: {black_count}, White cells: {grid_size**2 - black_count}")

    # Step 5: Detect numbers using pixel analysis
    print("Detecting clue numbers...")
    detected_numbers = detect_numbers_in_cells(warped_gray, grid_size, grid)
    print(f"  Detected {len(detected_numbers)} numbered cells (pixel method)")

    # Step 6: Refine grid using detected numbers
    grid = refine_grid_with_ocr_numbers(grid, detected_numbers, grid_size)

    # Step 7: Assign official numbers using crossword rules
    print("Assigning clue numbers by crossword rules...")
    numbers = assign_numbers(grid, grid_size)
    print(f"  Assigned {len(numbers)} numbers (rule-based)")

    # Compare detected vs rule-based
    if abs(len(detected_numbers) - len(numbers)) > 5:
        print(f"  WARNING: Pixel detection found {len(detected_numbers)} numbers "
              f"but rules assign {len(numbers)}. Grid classification may need tuning.")

    # Step 8: Output
    ascii_grid = grid_to_ascii(grid, numbers, grid_size)
    print("\n" + ascii_grid)

    result = grid_to_json(grid, numbers, grid_size, image_path)

    if debug:
        # Draw debug overlay on the FINAL refined grid (not the initial classification)
        debug_img = draw_debug_overlay(warped, grid, numbers, grid_size)

        # Write debug images to output/ sibling directory
        img_stem = Path(image_path).stem
        output_dir = Path(image_path).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        debug_path = str(output_dir / f"{img_stem}.debug.png")
        cv2.imwrite(debug_path, debug_img)
        print(f"\nDebug image saved: {debug_path}")

        warped_path = str(output_dir / f"{img_stem}.warped.png")
        cv2.imwrite(warped_path, warped)
        print(f"Warped grid saved: {warped_path}")

    return result


def find_grid_fallback(gray: np.ndarray) -> np.ndarray | None:
    """
    Fallback grid detection: use Hough lines to find a grid region,
    or try different thresholding methods.
    """
    # Try multiple threshold methods
    for block_size in [11, 15, 21, 31]:
        for C in [5, 10, 15]:
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, block_size, C
            )
            # Dilate to connect grid lines
            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(binary, kernel, iterations=2)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            for cnt in contours[:5]:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect = w / h if h > 0 else 0
                    area_ratio = cv2.contourArea(approx) / (gray.shape[0] * gray.shape[1])
                    if 0.6 < aspect < 1.5 and area_ratio > 0.05:
                        return approx

    # Last resort: use the whole image as the grid region
    h, w = gray.shape
    margin = int(min(h, w) * 0.02)
    return np.array([
        [margin, margin],
        [w - margin, margin],
        [w - margin, h - margin],
        [margin, h - margin],
    ]).reshape(4, 1, 2)


def main():
    parser = argparse.ArgumentParser(description="Extract crossword grid from a photo")
    parser.add_argument("image", help="Path to the crossword image")
    parser.add_argument("--output", "-o", help="Output JSON path (default: same name .grid.json)")
    parser.add_argument("--debug", "-d", action="store_true", help="Save debug images")
    parser.add_argument("--size", "-s", type=int, help="Override grid size (e.g., 15)")
    args = parser.parse_args()

    result = extract_crossword_grid(args.image, debug=args.debug)

    if args.size:
        print(f"\nNote: Grid size override not yet implemented. Detected: {result['grid_size']}")

    if args.output:
        output_path = args.output
    else:
        # Default: write to output/ sibling directory
        img_stem = Path(args.image).stem
        output_dir = Path(args.image).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{img_stem}.grid.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nGrid saved to: {output_path}")

    # Also save ASCII version
    ascii_path = str(Path(output_path).with_suffix(".txt"))
    grid = result["grid"]
    size = result["grid_size"]
    numbers = {}
    for r in range(size):
        for c in range(size):
            if grid[r][c] > 0:
                numbers[(r, c)] = grid[r][c]
    grid_chars = [["#" if v == 0 else "." for v in row] for row in grid]
    ascii_out = grid_to_ascii(grid_chars, numbers, size)
    with open(ascii_path, "w") as f:
        f.write(ascii_out + "\n")
    print(f"ASCII grid saved to: {ascii_path}")


if __name__ == "__main__":
    main()
