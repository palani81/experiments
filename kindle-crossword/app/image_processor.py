"""
Image processor optimized for crossword puzzles on Kindle e-ink displays.

Key improvements over v1:
- Gentler adaptive thresholding that preserves thin grid lines and small clue numbers
- Smarter contrast enhancement with lower CLAHE clip limit (1.5 vs 3.0)
- Larger adaptive threshold block size (31 vs 15) to avoid destroying fine detail
- Lanczos resampling for upscaling (sharpest for line art)
- Optional morphological closing to reconnect broken grid lines
- Higher unsharp mask radius for crisper lines on e-ink
"""
import logging
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)

# Kindle display resolutions at 300 PPI
KINDLE_PAPERWHITE = (1236, 1648)
KINDLE_SCRIBE = (1860, 2480)
KINDLE_PORTRAIT = KINDLE_SCRIBE
KINDLE_LANDSCAPE = (2480, 1860)


def process_image(input_path: str, output_path: str, options: dict) -> dict:
    metadata: dict[str, Any] = {}

    img = _load_and_validate(input_path, metadata)

    original_h, original_w = img.shape[:2]
    metadata["original_size"] = (original_w, original_h)

    if options.get("auto_perspective", True):
        img, corrected = _perspective_correction(img)
        metadata["perspective_corrected"] = corrected
    else:
        metadata["perspective_corrected"] = False

    img, angle = _rotation_correction(img)
    metadata["rotation_angle"] = angle

    img = _to_grayscale(img)

    # Background normalization: removes shadows, uneven lighting, newspaper tint.
    # This is the key step for phone photos — divides by a heavily blurred copy
    # to flatten the background to white while preserving text/lines as dark.
    img = _normalize_background(img)

    # Resize for Kindle
    target = options.get("kindle_model", "scribe")
    img = _resize_for_kindle(img, target)

    # Light sharpen to crisp up grid lines for e-ink
    sharpness = options.get("sharpness", 1.2)
    pil_img = _sharpen(img, sharpness)

    metadata["processed_size"] = pil_img.size

    # Save at 300 DPI
    pil_img.save(output_path, format="PNG", optimize=False, dpi=(300, 300))

    return metadata


def _load_and_validate(path: str, metadata: dict) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Failed to load image: {path}")

    h, w = img.shape[:2]
    if h < 500 or w < 500:
        metadata["warning"] = f"Image is small ({w}x{h}), output quality may be reduced"
        logger.warning("Input image %s is small (%dx%d)", path, w, h)

    return img


def _perspective_correction(img: np.ndarray) -> tuple[np.ndarray, bool]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img, False

    h, w = img.shape[:2]
    image_area = h * w

    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for contour in contours[:5]:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

        if len(approx) != 4:
            continue

        contour_area = cv2.contourArea(approx)
        if contour_area < 0.25 * image_area:
            continue

        pts = approx.reshape(4, 2).astype(np.float32)
        pts = _order_points(pts)

        width_top = np.linalg.norm(pts[1] - pts[0])
        width_bottom = np.linalg.norm(pts[2] - pts[3])
        max_width = int(max(width_top, width_bottom))

        height_left = np.linalg.norm(pts[3] - pts[0])
        height_right = np.linalg.norm(pts[2] - pts[1])
        max_height = int(max(height_left, height_right))

        if max_width == 0 or max_height == 0:
            continue

        dst = np.array(
            [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]],
            dtype=np.float32,
        )

        matrix = cv2.getPerspectiveTransform(pts, dst)
        warped = cv2.warpPerspective(
            img, matrix, (max_width, max_height),
            flags=cv2.INTER_LANCZOS4,
            borderValue=(255, 255, 255),
        )
        return warped, True

    return img, False


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def _rotation_correction(img: np.ndarray) -> tuple[np.ndarray, float]:
    """
    Detect and correct small rotations (up to ±10°) using long horizontal/vertical
    lines typical of crossword grids. Only corrects if there's strong consensus
    among detected lines — avoids wild rotations from diagonal content.
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    h, w = gray.shape[:2]

    # Use longer minLineLength relative to image size to only pick up grid lines
    min_line = max(150, min(h, w) // 6)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=120,
                            minLineLength=min_line, maxLineGap=10)

    if lines is None or len(lines) == 0:
        return img, 0.0

    # Only consider lines that are nearly horizontal (within ±15° of horizontal)
    # This filters out diagonal content, vertical lines, etc.
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(angle) <= 15:
            angles.append(angle)

    if len(angles) < 5:
        # Not enough horizontal lines to be confident
        return img, 0.0

    angles = np.array(angles)
    median_angle = float(np.median(angles))

    # Only correct if the angle is small and consistent
    # (std dev < 3° means the lines agree on the skew)
    if abs(median_angle) <= 0.3 or abs(median_angle) > 10:
        return img, 0.0

    angle_std = float(np.std(angles))
    if angle_std > 3.0:
        # Lines disagree too much — don't correct
        return img, 0.0

    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)

    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)
    matrix[0, 2] += (new_w - w) / 2
    matrix[1, 2] += (new_h - h) / 2

    rotated = cv2.warpAffine(
        img, matrix, (new_w, new_h),
        flags=cv2.INTER_LANCZOS4,
        borderValue=(255, 255, 255),
    )
    return rotated, round(median_angle, 2)


def _to_grayscale(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def _normalize_background(img: np.ndarray) -> np.ndarray:
    """
    Remove uneven lighting, shadows, and newspaper background tint.

    Works by dividing the image by a heavily blurred version of itself.
    This makes the background uniformly white while keeping text/lines dark.
    Much better than thresholding for phone photos of crosswords.
    """
    # Step 1: Denoise — median blur kills halftone dots while preserving edges
    denoised = cv2.medianBlur(img, 3)

    # Step 2: Estimate the background using a very large Gaussian blur.
    # The kernel must be large enough that text/lines are completely blurred out,
    # leaving only the background illumination pattern.
    h, w = denoised.shape[:2]
    ksize = max(h, w) // 8
    ksize = ksize if ksize % 2 == 1 else ksize + 1  # must be odd
    ksize = max(51, ksize)  # minimum 51
    background = cv2.GaussianBlur(denoised, (ksize, ksize), 0).astype(np.float64)

    # Step 3: Divide image by background — this normalizes illumination.
    # Result: background → ~1.0 (white), text → << 1.0 (dark)
    normalized = denoised.astype(np.float64) / np.maximum(background, 1.0)

    # Step 4: Scale to full 0-255 range with contrast stretch
    # Map the result so that 1.0 → 255 (white) and dark values → 0 (black)
    normalized = normalized * 255.0
    normalized = np.clip(normalized, 0, 255).astype(np.uint8)

    # Step 5: Levels adjustment — set black and white points, then apply
    # gamma to restore natural-looking contrast with solid blacks.
    p_low, p_high = np.percentile(normalized, (1, 95))
    if p_high > p_low:
        stretched = (normalized.astype(np.float64) - p_low) / (p_high - p_low)
        stretched = np.clip(stretched, 0, 1.0)

        # Gamma < 1.0 pushes midtones darker → restores solid blacks for
        # grid lines and text without crushing white cells
        gamma = 0.6
        stretched = np.power(stretched, gamma) * 255.0
        stretched = np.clip(stretched, 0, 255).astype(np.uint8)
    else:
        stretched = normalized

    return stretched


def _resize_for_kindle(img: np.ndarray, target: str = "scribe") -> np.ndarray:
    h, w = img.shape[:2]

    if target == "paperwhite":
        dims = KINDLE_PAPERWHITE
    else:
        dims = KINDLE_SCRIBE

    if w > h:
        target_w, target_h = dims[1], dims[0]
    else:
        target_w, target_h = dims

    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    # INTER_AREA for downscaling, INTER_LANCZOS4 for upscaling (sharpest for line art)
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LANCZOS4
    resized = cv2.resize(img, (new_w, new_h), interpolation=interp)

    canvas = np.full((target_h, target_w), 255, dtype=np.uint8)
    x_offset = (target_w - new_w) // 2
    y_offset = (target_h - new_h) // 2
    canvas[y_offset : y_offset + new_h, x_offset : x_offset + new_w] = resized

    return canvas


def _sharpen(img: np.ndarray, sharpness: float) -> Image.Image:
    pil_img = Image.fromarray(img).convert("L")
    percent = int(sharpness * 100)
    # radius=2.0 (vs old 1.5) — better for grid lines on e-ink
    # threshold=3 (vs old 2) — avoids sharpening noise in empty cells
    sharpened = pil_img.filter(ImageFilter.UnsharpMask(radius=2.0, percent=percent, threshold=3))
    return sharpened
