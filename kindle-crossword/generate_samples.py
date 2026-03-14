#!/usr/bin/env python3
"""
Generate sample crossword puzzle images optimized for Kindle e-ink displays.

Produces high-resolution (300 DPI) grayscale PNGs and a combined PDF.
Each puzzle includes the grid with clue numbers and clue lists below.

Usage:
    python generate_samples.py

Output:
    output/sample_1_puzzle.png      - Blank puzzle grid
    output/sample_1_answers.png     - Grid with answers filled in
    output/sample_2_puzzle.png      - Second puzzle
    output/sample_2_answers.png     - Second puzzle answers
    ...
    output/crosswords_for_kindle.pdf - All puzzles combined
"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# Kindle Scribe at 300 DPI
TARGET_W = 1860
TARGET_H = 2480


# ── Puzzle data ──────────────────────────────────────────────────────────────

PUZZLES = [
    {
        "title": "Tech Talk",
        "words": [
            ("PYTHON", "Popular programming language named after a comedy troupe"),
            ("CLOUD", "Where AWS and Azure live"),
            ("DEBUG", "Find and fix errors in code"),
            ("PIXEL", "Smallest unit of a digital image"),
            ("CACHE", "Fast temporary storage"),
            ("LINUX", "Open-source operating system"),
            ("BYTE", "Eight bits"),
            ("STACK", "LIFO data structure"),
            ("NODE", "Point in a network or tree"),
            ("QUERY", "Database search request"),
            ("ARRAY", "Ordered collection of elements"),
            ("LOGIC", "Foundation of Boolean algebra"),
            ("PARSE", "Analyze string syntax"),
            ("TOKEN", "Authentication credential"),
            ("ROUTE", "URL path in a web app"),
        ],
    },
    {
        "title": "Kitchen Classics",
        "words": [
            ("BRAISE", "Slow-cook in liquid after browning"),
            ("WHISK", "Beat eggs or cream with this"),
            ("SAUTE", "Cook quickly in a small amount of fat"),
            ("KNEAD", "Work dough with your hands"),
            ("BLEND", "Mix ingredients until smooth"),
            ("CHOP", "Cut into irregular pieces"),
            ("GRILL", "Cook over direct high heat"),
            ("POACH", "Cook gently in simmering liquid"),
            ("BASTE", "Spoon drippings over roasting meat"),
            ("MINCE", "Cut into very fine pieces"),
            ("GLAZE", "Apply a shiny coating"),
            ("ROAST", "Cook in an oven with dry heat"),
            ("STEEP", "Soak in hot water to extract flavor"),
            ("DICE", "Cut into small cubes"),
        ],
    },
    {
        "title": "World Capitals",
        "words": [
            ("TOKYO", "Capital of Japan"),
            ("PARIS", "City of Light"),
            ("CAIRO", "Capital on the Nile"),
            ("LIMA", "Capital of Peru"),
            ("ROME", "Eternal City"),
            ("OSLO", "Capital of Norway"),
            ("DELHI", "Capital region of India"),
            ("BERN", "Capital of Switzerland"),
            ("QUITO", "Highest official capital city"),
            ("KYIV", "Capital of Ukraine"),
            ("ACCRA", "Capital of Ghana"),
            ("MINSK", "Capital of Belarus"),
            ("DAKAR", "Capital of Senegal"),
            ("RABAT", "Capital of Morocco"),
        ],
    },
    {
        "title": "Music & Rhythm",
        "words": [
            ("TEMPO", "Speed of a musical piece"),
            ("CHORD", "Three or more notes played together"),
            ("PITCH", "How high or low a note sounds"),
            ("SCALE", "Ordered sequence of notes"),
            ("SHARP", "Half step higher in pitch"),
            ("BASS", "Lowest vocal range"),
            ("CLEF", "Symbol at start of a staff"),
            ("FORTE", "Play loudly (musical direction)"),
            ("LYRIC", "Words of a song"),
            ("OCTAVE", "Interval of eight notes"),
            ("MINOR", "Sad-sounding key or scale"),
            ("TENOR", "High male vocal range"),
            ("FUGUE", "Contrapuntal composition"),
            ("CODA", "Concluding passage"),
        ],
    },
]


# ── Crossword engine ────────────────────────────────────────────────────────

class PlacedWord:
    def __init__(self, word, clue, row, col, direction, number=0):
        self.word = word
        self.clue = clue
        self.row = row
        self.col = col
        self.direction = direction
        self.number = number


class CrosswordGrid:
    def __init__(self, size=15):
        self.size = size
        self.grid = [[None] * size for _ in range(size)]
        self.placed: list[PlacedWord] = []

    def can_place(self, word, row, col, direction):
        dr = 0 if direction == "across" else 1
        dc = 1 if direction == "across" else 0
        length = len(word)

        end_r = row + dr * (length - 1)
        end_c = col + dc * (length - 1)
        if end_r >= self.size or end_c >= self.size or row < 0 or col < 0:
            return False

        # Cell before word must be empty/boundary
        br, bc = row - dr, col - dc
        if 0 <= br < self.size and 0 <= bc < self.size and self.grid[br][bc] is not None:
            return False
        # Cell after word must be empty/boundary
        ar, ac = row + dr * length, col + dc * length
        if 0 <= ar < self.size and 0 <= ac < self.size and self.grid[ar][ac] is not None:
            return False

        has_cross = False
        for i in range(length):
            r = row + dr * i
            c = col + dc * i
            cell = self.grid[r][c]
            if cell is not None:
                if cell != word[i]:
                    return False
                has_cross = True
            else:
                # No parallel adjacency
                for pr, pc in [(r + dc, c + dr), (r - dc, c - dr)]:
                    if 0 <= pr < self.size and 0 <= pc < self.size:
                        if self.grid[pr][pc] is not None:
                            return False

        if self.placed and not has_cross:
            return False
        return True

    def place(self, word, clue, row, col, direction):
        dr = 0 if direction == "across" else 1
        dc = 1 if direction == "across" else 0
        for i in range(len(word)):
            self.grid[row + dr * i][col + dc * i] = word[i]
        pw = PlacedWord(word, clue, row, col, direction)
        self.placed.append(pw)

    def assign_numbers(self):
        starts = {}
        for pw in self.placed:
            key = (pw.row, pw.col)
            starts.setdefault(key, []).append(pw)
        num = 1
        for pos in sorted(starts):
            for pw in starts[pos]:
                pw.number = num
            num += 1

    def bounds(self):
        min_r = min_c = self.size
        max_r = max_c = 0
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] is not None:
                    min_r, min_c = min(min_r, r), min(min_c, c)
                    max_r, max_c = max(max_r, r), max(max_c, c)
        return min_r, min_c, max_r, max_c


def build_crossword(word_clues, grid_size=17, attempts=80):
    best = None
    for _ in range(attempts):
        g = CrosswordGrid(grid_size)
        order = list(word_clues)
        random.shuffle(order)

        w0, c0 = order[0]
        w0 = w0.upper()
        center = grid_size // 2
        g.place(w0, c0, center, max(0, center - len(w0) // 2), "across")

        for w, c in order[1:]:
            w = w.upper()
            positions = []
            for d in ("across", "down"):
                for r in range(grid_size):
                    for col in range(grid_size):
                        if g.can_place(w, r, col, d):
                            dist = abs(r - center) + abs(col - center)
                            positions.append((r, col, d, dist))
            if positions:
                positions.sort(key=lambda x: x[3])
                top = positions[: max(1, len(positions) // 4)]
                r, col, d, _ = random.choice(top)
                g.place(w, c, r, col, d)

        if best is None or len(g.placed) > len(best.placed):
            best = g
        if len(best.placed) == len(word_clues):
            break

    best.assign_numbers()
    return best


# ── Renderer ─────────────────────────────────────────────────────────────────

def _get_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_crossword(grid: CrosswordGrid, title: str, show_answers=False,
                     width=TARGET_W, height=TARGET_H):
    """Render a crossword grid as a high-res grayscale image."""
    min_r, min_c, max_r, max_c = grid.bounds()
    nrows = max_r - min_r + 1
    ncols = max_c - min_c + 1

    margin = int(width * 0.05)
    title_h = int(height * 0.045)
    clue_h = int(height * 0.32)
    grid_area_w = width - 2 * margin
    grid_area_h = height - 2 * margin - title_h - clue_h

    cell = min(grid_area_w // ncols, grid_area_h // nrows, int(width * 0.06))
    gw = cell * ncols
    gh = cell * nrows
    gx = (width - gw) // 2
    gy = margin + title_h + 10

    line_w = max(3, cell // 18)
    num_sz = max(16, cell // 4)
    let_sz = max(22, cell * 2 // 5)
    ttl_sz = max(40, width // 22)
    clue_sz = max(24, width // 50)

    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    # Title
    tf = _get_font(ttl_sz, bold=True)
    tb = draw.textbbox((0, 0), title, font=tf)
    draw.text(((width - tb[2] + tb[0]) // 2, margin // 2), title, fill=0, font=tf)

    nf = _get_font(num_sz)
    lf = _get_font(let_sz, bold=True)
    cf = _get_font(clue_sz)
    cbf = _get_font(clue_sz, bold=True)

    # Grid cells
    for r in range(nrows):
        for c in range(ncols):
            gr, gc = r + min_r, c + min_c
            x, y = gx + c * cell, gy + r * cell

            if grid.grid[gr][gc] is not None:
                draw.rectangle([x, y, x + cell, y + cell], fill=255, outline=0, width=line_w)

                # Clue number
                for pw in grid.placed:
                    if pw.row == gr and pw.col == gc and pw.number > 0:
                        draw.text((x + 5, y + 3), str(pw.number), fill=0, font=nf)
                        break

                if show_answers:
                    ch = grid.grid[gr][gc]
                    lb = draw.textbbox((0, 0), ch, font=lf)
                    lw, lh = lb[2] - lb[0], lb[3] - lb[1]
                    draw.text(
                        (x + (cell - lw) // 2, y + (cell - lh) // 2 + num_sz // 4),
                        ch, fill=0, font=lf,
                    )
            else:
                draw.rectangle([x, y, x + cell, y + cell], fill=0)

    # Clues
    clue_top = gy + gh + int(margin * 0.6)
    across = sorted([p for p in grid.placed if p.direction == "across"], key=lambda p: p.number)
    down = sorted([p for p in grid.placed if p.direction == "down"], key=lambda p: p.number)

    col_w = (width - 2 * margin - 30) // 2
    line_h = int(clue_sz * 1.45)

    # ACROSS
    draw.text((margin, clue_top), "ACROSS", fill=0, font=cbf)
    cy = clue_top + line_h + 2
    for pw in across:
        for line in _wrap(draw, f"{pw.number}. {pw.clue}", cf, col_w):
            if cy + line_h > height - margin // 2:
                break
            draw.text((margin + 12, cy), line, fill=0, font=cf)
            cy += line_h

    # Separator
    sep_x = margin + col_w + 15
    draw.line([(sep_x, clue_top), (sep_x, height - margin)], fill=140, width=2)

    # DOWN
    dx = sep_x + 15
    cy = clue_top
    draw.text((dx, cy), "DOWN", fill=0, font=cbf)
    cy += line_h + 2
    for pw in down:
        for line in _wrap(draw, f"{pw.number}. {pw.clue}", cf, col_w):
            if cy + line_h > height - margin // 2:
                break
            draw.text((dx + 12, cy), line, fill=0, font=cf)
            cy += line_h

    return img


def generate_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_images = []

    for i, puzzle in enumerate(PUZZLES, 1):
        print(f"Generating puzzle {i}: {puzzle['title']}...")
        grid = build_crossword(puzzle["words"])
        print(f"  Placed {len(grid.placed)}/{len(puzzle['words'])} words")

        # Blank puzzle
        img_puzzle = render_crossword(grid, puzzle["title"], show_answers=False)
        puzzle_path = os.path.join(OUTPUT_DIR, f"sample_{i}_puzzle.png")
        img_puzzle.save(puzzle_path, "PNG", dpi=(300, 300))
        all_images.append(puzzle_path)

        # Answer key
        img_answers = render_crossword(grid, f"{puzzle['title']} — Answers", show_answers=True)
        answer_path = os.path.join(OUTPUT_DIR, f"sample_{i}_answers.png")
        img_answers.save(answer_path, "PNG", dpi=(300, 300))
        all_images.append(answer_path)

        print(f"  Saved: {puzzle_path}")
        print(f"  Saved: {answer_path}")

    # Combined PDF
    pdf_path = os.path.join(OUTPUT_DIR, "crosswords_for_kindle.pdf")
    page_w = 6.2 * inch
    page_h = 8.267 * inch
    c = rl_canvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    for img_path in all_images:
        c.drawImage(img_path, 0, 0, width=page_w, height=page_h,
                    preserveAspectRatio=True, anchor="c")
        c.showPage()
    c.save()
    print(f"\nCombined PDF: {pdf_path}")
    print(f"Total images: {len(all_images)}")

    return all_images


if __name__ == "__main__":
    random.seed(42)  # Reproducible for review
    generate_all()
