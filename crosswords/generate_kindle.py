#!/usr/bin/env python3
"""
Kindle Scribe Crossword Generator
==================================
Generates an HTML crossword page optimized for the Kindle Scribe's
e-ink display and pen input.

Usage:
    python3 generate_kindle.py puzzles/<puzzle>.json [--output <path>]

Output: A self-contained HTML file suitable for the Kindle Scribe browser
        or for converting to PDF via print/save.

Kindle Scribe specs:
  - 10.2" e-ink display, 1860 x 2480 px (300 ppi)
  - Pen input (stylus writing on screen)
  - Basic WebKit browser
  - No color — pure black/white/gray
"""

import argparse
import json
import sys
from pathlib import Path


def load_puzzle(path: str) -> dict:
    """Load puzzle JSON file."""
    with open(path) as f:
        return json.load(f)


def build_grid_data(puzzle: dict) -> list[list[dict]]:
    """Build a 2D grid structure from puzzle data.

    Each cell is a dict: {"type": "black"|"white", "number": int|None}
    """
    meta = puzzle["metadata"]
    rows = meta.get("grid_rows", meta["grid_size"])
    cols = meta.get("grid_cols", meta["grid_size"])

    # Parse from the manually verified grid in the txt file
    txt_path = str(Path(path).with_suffix(".txt"))
    try:
        grid = parse_grid_from_txt(txt_path, rows, cols)
    except Exception as e:
        print(f"  Warning: grid parse failed ({e}), using empty grid")
        grid = [[{"type": "white", "number": None} for _ in range(cols)] for _ in range(rows)]

    return grid


def parse_grid_from_txt(txt_path: str, rows: int, cols: int) -> list[list[dict]]:
    """Parse the grid structure from the ASCII art in the .txt file."""
    with open(txt_path) as f:
        lines = f.readlines()

    grid = [[{"type": "white", "number": None} for _ in range(cols)] for _ in range(rows)]
    grid_row = 0

    for line in lines:
        line = line.rstrip()
        if "│" not in line:
            continue
        # Skip separator lines (contain ┬, ┼, ┤, ┴)
        if "┬" in line or "┼" in line or "┴" in line:
            continue

        # Split by │ — first part is row label, last is trailing empty
        parts = line.split("│")
        cell_parts = parts[1:-1] if len(parts) > 2 else parts[1:]

        if len(cell_parts) != cols:
            continue

        for col, cell in enumerate(cell_parts):
            cell_content = cell.strip()
            if "███" in cell or "███" in cell_content:
                grid[grid_row][col]["type"] = "black"
            elif cell_content == "":
                pass
            else:
                try:
                    num = int(cell_content)
                    grid[grid_row][col]["number"] = num
                except ValueError:
                    pass

        grid_row += 1
        if grid_row >= rows:
            break

    if grid_row < rows:
        raise ValueError(f"Only parsed {grid_row}/{rows} grid rows from {txt_path}")

    return grid


def reconstruct_grid(puzzle: dict, size: int) -> list[list[dict]]:
    """Reconstruct grid from clue data (fallback)."""
    grid = [[{"type": "white", "number": None} for _ in range(size)] for _ in range(size)]
    # This is a simplified reconstruction — mark everything white
    # and place numbers based on across/down starts
    return grid


def generate_html(puzzle: dict, grid: list[list[dict]]) -> str:
    """Generate Kindle Scribe-optimized HTML."""
    meta = puzzle["metadata"]
    rows = meta.get("grid_rows", meta["grid_size"])
    cols = meta.get("grid_cols", meta["grid_size"])
    clues = puzzle["clues"]
    date = meta.get("date", "")
    author = meta.get("author", "")
    title = meta.get("title", "The Daily Crossword")

    # Build grid HTML
    grid_html = build_grid_html(grid, rows, cols)

    # Build clue lists
    across_html = build_clue_list(clues["across"], "Across")
    down_html = build_clue_list(clues["down"], "Down")

    # Cell size calculation for Kindle Scribe
    # Target: grid takes about 60% of the page width
    # At 1860px width, 60% = ~1116px, for 15 cells = ~74px per cell
    cell_size = 46  # px — good balance for 15x15 on Kindle

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — {date}</title>
<style>
  @page {{
    size: 1860px 2480px;
    margin: 0;
  }}

  * {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }}

  body {{
    font-family: Georgia, 'Times New Roman', serif;
    background: #fff;
    color: #000;
    width: 100%;
    max-width: 1860px;
    margin: 0 auto;
    padding: 24px 32px;
    -webkit-text-size-adjust: none;
  }}

  /* Header */
  .header {{
    text-align: center;
    margin-bottom: 16px;
    border-bottom: 2px solid #000;
    padding-bottom: 10px;
  }}
  .header h1 {{
    font-size: 28px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  .header .meta {{
    font-size: 16px;
    color: #333;
    margin-top: 4px;
  }}

  /* Grid */
  .grid-container {{
    display: flex;
    justify-content: center;
    margin: 16px 0;
  }}

  table.grid {{
    border-collapse: collapse;
    border: 3px solid #000;
  }}

  table.grid td {{
    width: {cell_size}px;
    height: {cell_size}px;
    border: 1px solid #000;
    position: relative;
    vertical-align: top;
    padding: 0;
    background: #fff;
  }}

  table.grid td.black {{
    background: #000;
    border-color: #000;
  }}

  table.grid td .num {{
    position: absolute;
    top: 1px;
    left: 2px;
    font-size: 11px;
    font-weight: bold;
    line-height: 1;
    color: #000;
    font-family: Arial, Helvetica, sans-serif;
  }}

  /* Clues section */
  .clues-container {{
    display: flex;
    gap: 32px;
    margin-top: 16px;
  }}

  .clue-section {{
    flex: 1;
  }}

  .clue-section h2 {{
    font-size: 20px;
    font-weight: bold;
    text-transform: uppercase;
    border-bottom: 2px solid #000;
    padding-bottom: 4px;
    margin-bottom: 8px;
  }}

  .clue-list {{
    list-style: none;
    padding: 0;
    column-count: 2;
    column-gap: 20px;
  }}

  .clue-list li {{
    font-size: 14px;
    line-height: 1.35;
    margin-bottom: 4px;
    break-inside: avoid;
    -webkit-column-break-inside: avoid;
  }}

  .clue-list li .clue-num {{
    font-weight: bold;
    display: inline-block;
    min-width: 24px;
    text-align: right;
    margin-right: 4px;
  }}

  /* Print styles */
  @media print {{
    body {{
      padding: 0;
    }}
    .header {{
      margin-bottom: 12px;
    }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>{title}</h1>
  <div class="meta">{date} &middot; By {author}</div>
</div>

<div class="grid-container">
{grid_html}
</div>

<div class="clues-container">
  <div class="clue-section">
    <h2>Across</h2>
{across_html}
  </div>
  <div class="clue-section">
    <h2>Down</h2>
{down_html}
  </div>
</div>

</body>
</html>"""

    return html


def build_grid_html(grid: list[list[dict]], num_rows: int, num_cols: int) -> str:
    """Build the HTML table for the crossword grid."""
    rows = []
    for r in range(num_rows):
        cells = []
        for c in range(num_cols):
            cell = grid[r][c]
            if cell["type"] == "black":
                cells.append('    <td class="black"></td>')
            else:
                num_span = ""
                if cell["number"]:
                    num_span = f'<span class="num">{cell["number"]}</span>'
                cells.append(f'    <td>{num_span}</td>')
        rows.append("  <tr>\n" + "\n".join(cells) + "\n  </tr>")

    return '<table class="grid">\n' + "\n".join(rows) + "\n</table>"


def build_clue_list(clues: dict, label: str) -> str:
    """Build HTML list for a set of clues."""
    items = []
    for num in sorted(clues.keys(), key=lambda x: int(x)):
        text = clues[num]
        # Escape HTML special chars
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        items.append(f'    <li><span class="clue-num">{num}</span> {text}</li>')
    return '    <ul class="clue-list">\n' + "\n".join(items) + "\n    </ul>"


def main():
    global path
    parser = argparse.ArgumentParser(description="Generate Kindle Scribe crossword HTML")
    parser.add_argument("puzzle", help="Path to puzzle JSON file")
    parser.add_argument("--output", "-o", help="Output HTML path")
    args = parser.parse_args()

    path = args.puzzle
    puzzle = load_puzzle(path)

    print(f"Loading puzzle: {path}")
    meta = puzzle["metadata"]
    print(f"  {meta.get('title', 'Crossword')} — {meta.get('date', '?')} by {meta.get('author', '?')}")
    rows = meta.get("grid_rows", meta["grid_size"])
    cols = meta.get("grid_cols", meta["grid_size"])
    print(f"  Grid: {rows}x{cols}, {meta.get('total_clues', '?')} clues")

    grid = build_grid_data(puzzle)

    html = generate_html(puzzle, grid)

    if args.output:
        output_path = args.output
    else:
        stem = Path(path).stem
        output_dir = Path(path).parent.parent / "kindle"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{stem}.html")

    with open(output_path, "w") as f:
        f.write(html)
    print(f"\nKindle HTML saved to: {output_path}")


if __name__ == "__main__":
    main()
