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
    num_rows = meta.get("grid_rows", meta["grid_size"])
    cols = meta.get("grid_cols", meta["grid_size"])
    clues = puzzle["clues"]
    date = meta.get("date", "")
    author = meta.get("author", "")
    title = meta.get("title", "The Daily Crossword")

    # Format the date nicely
    try:
        from datetime import datetime
        dt = datetime.strptime(date, "%Y-%m-%d")
        date_display = dt.strftime("%A, %B %-d, %Y")
    except Exception:
        date_display = date

    # Build grid HTML
    grid_html = build_grid_html(grid, num_rows, cols)

    # Build clue lists
    across_html = build_clue_list(clues["across"], "Across")
    down_html = build_clue_list(clues["down"], "Down")

    # Cell size — 46px works well for 15-col grids on Kindle Scribe
    cell_size = 46

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} &mdash; {date}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: Georgia, 'Times New Roman', serif;
    background: #fff;
    color: #000;
    max-width: 800px;
    margin: 0 auto;
    padding: 16px 20px;
    -webkit-text-size-adjust: none;
  }}

  /* Navigation */
  .nav {{
    margin-bottom: 12px;
  }}
  .nav a {{
    font-size: 15px;
    color: #000;
    text-decoration: none;
    font-family: Arial, Helvetica, sans-serif;
  }}
  .nav a::before {{
    content: "\\25C0\\00A0";
  }}

  /* Header */
  .header {{
    text-align: center;
    margin-bottom: 14px;
    border-bottom: 3px solid #000;
    padding-bottom: 8px;
  }}
  .header h1 {{
    font-size: 26px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  .header .date {{
    font-size: 18px;
    font-weight: bold;
    margin-top: 2px;
  }}
  .header .author {{
    font-size: 14px;
    color: #444;
    margin-top: 2px;
  }}

  /* Grid */
  .grid-wrap {{
    text-align: center;
    margin: 14px 0;
  }}

  table.grid {{
    border-collapse: collapse;
    border: 3px solid #000;
    display: inline-table;
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

  table.grid td .n {{
    position: absolute;
    top: 1px;
    left: 2px;
    font-size: 10px;
    font-weight: bold;
    line-height: 1;
    color: #000;
    font-family: Arial, Helvetica, sans-serif;
  }}

  /* Clues */
  .clues {{
    display: flex;
    gap: 24px;
    margin-top: 14px;
  }}

  .clues section {{
    flex: 1;
  }}

  .clues h2 {{
    font-size: 18px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 2px solid #000;
    padding-bottom: 3px;
    margin-bottom: 6px;
  }}

  .clues ul {{
    list-style: none;
    padding: 0;
  }}

  .clues li {{
    font-size: 13px;
    line-height: 1.3;
    margin-bottom: 3px;
    break-inside: avoid;
  }}

  .clues li b {{
    display: inline-block;
    min-width: 22px;
    text-align: right;
    margin-right: 4px;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 12px;
  }}

  /* Print */
  @media print {{
    .nav {{ display: none; }}
    body {{ padding: 0; }}
  }}
</style>
</head>
<body>

<div class="nav"><a href="index.html">All Puzzles</a></div>

<div class="header">
  <h1>{title}</h1>
  <div class="date">{date_display}</div>
  <div class="author">By {author}</div>
</div>

<div class="grid-wrap">
{grid_html}
</div>

<div class="clues">
  <section>
    <h2>Across</h2>
{across_html}
  </section>
  <section>
    <h2>Down</h2>
{down_html}
  </section>
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
                cells.append('<td class="black"></td>')
            else:
                if cell["number"]:
                    cells.append(f'<td><span class="n">{cell["number"]}</span></td>')
                else:
                    cells.append('<td></td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")

    return '<table class="grid">\n' + "\n".join(rows) + "\n</table>"


def build_clue_list(clues: dict, label: str) -> str:
    """Build HTML list for a set of clues."""
    items = []
    for num in sorted(clues.keys(), key=lambda x: int(x)):
        text = clues[num]
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        items.append(f'    <li><b>{num}</b> {text}</li>')
    return '    <ul>\n' + "\n".join(items) + "\n    </ul>"


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
