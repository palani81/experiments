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
import shutil
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


def generate_html(puzzle: dict, grid: list[list[dict]], photo_filenames: list[str] | None = None) -> str:
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

    # Build source photo links
    photo_links_html = ""
    if photo_filenames:
        links = []
        for i, fname in enumerate(photo_filenames):
            label = f"Source photo {i + 1}" if len(photo_filenames) > 1 else "Source photo"
            links.append(f'<a href="{fname}">{label}</a>')
        photo_links_html = '  <div class="source-photos">' + " | ".join(links) + '</div>'

    # Build clue data as JSON for the interactive banner
    clues_json = json.dumps(clues)

    # Build grid HTML
    grid_html = build_grid_html(grid, num_rows, cols)

    # Build clue lists
    across_html = build_clue_list(clues["across"], "Across")
    down_html = build_clue_list(clues["down"], "Down")

    # Grid width as percentage of container so it scales on any screen
    # Each cell uses aspect-ratio: 1 to guarantee square
    col_pct = round(100 / cols, 4)

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
  .nav {{ margin-bottom: 12px; }}
  .nav a {{
    font-size: 15px;
    color: #000;
    text-decoration: none;
    font-family: Arial, Helvetica, sans-serif;
  }}
  .nav a::before {{ content: "\\25C0\\00A0"; }}

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
  .header .date {{ font-size: 18px; font-weight: bold; margin-top: 2px; }}
  .header .author {{ font-size: 14px; color: #444; margin-top: 2px; }}
  .header .source-photos {{ font-size: 12px; margin-top: 4px; }}
  .header .source-photos a {{ color: #333; }}

  /* Grid — uses table layout for maximum e-reader compatibility */
  .grid-wrap {{
    text-align: center;
    margin: 14px 0;
  }}

  .grid {{
    display: inline-table;
    border-collapse: collapse;
    border: 3px solid #000;
    max-width: 690px;
    width: 100%;
    table-layout: fixed;
  }}

  .grid-row {{
    display: table-row;
  }}

  .cell {{
    display: table-cell;
    border: 1px solid #000;
    position: relative;
    background: #fff;
    vertical-align: top;
    width: {col_pct}%;
    /* padding-bottom trick for square cells (aspect-ratio fallback) */
    height: 0;
    padding-bottom: {col_pct}%;
  }}

  .cell.black {{
    background: #000;
    border-color: #000;
  }}

  .cell .n {{
    position: absolute;
    top: 1px;
    left: 2px;
    font-size: 10px;
    font-weight: bold;
    line-height: 1;
    color: #000;
    font-family: Arial, Helvetica, sans-serif;
    z-index: 1;
    pointer-events: none;
  }}

  /* Writable input in each white cell */
  .cell input {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: none;
    background: transparent;
    text-align: center;
    font-size: 22px;
    font-weight: bold;
    font-family: Arial, Helvetica, sans-serif;
    text-transform: uppercase;
    padding-top: 18%;
    color: #000;
    outline: none;
    -webkit-appearance: none;
    appearance: none;
    border-radius: 0;
  }}

  .cell input:focus {{
    background: #eee;
  }}

  /* Clues */
  .clues {{
    display: flex;
    gap: 24px;
    margin-top: 14px;
  }}

  .clues section {{ flex: 1; }}

  .clues h2 {{
    font-size: 18px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 2px solid #000;
    padding-bottom: 3px;
    margin-bottom: 6px;
  }}

  .clues ul {{ list-style: none; padding: 0; }}

  .clues li {{
    font-size: 16px;
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

  /* Clue banner — sticky at top, shows clue for focused cell */
  #clue-banner {{
    position: sticky;
    top: 0;
    z-index: 10;
    background: #f0f0f0;
    border: 2px solid #000;
    padding: 6px 10px;
    font-size: 14px;
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.3;
    min-height: 32px;
    display: none;
  }}
  #clue-banner.visible {{ display: block; }}
  #clue-banner .clue-dir {{ font-weight: bold; text-transform: uppercase; }}

  /* Print */
  @media print {{
    .nav {{ display: none; }}
    #clue-banner {{ display: none; }}
    body {{ padding: 0; }}
    .cell input {{ padding-top: 25%; }}
  }}
</style>
</head>
<body>

<div class="nav"><a href="index.html">All Puzzles</a></div>

<div class="header">
  <h1>{title}</h1>
  <div class="date">{date_display}</div>
  <div class="author">By {author}</div>
{photo_links_html}
</div>

<div id="clue-banner"></div>

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

<script>
(function() {{
  var CLUES = {clues_json};
  var COLS = {cols};
  var STORAGE_KEY = 'crossword_{date}';
  var banner = document.getElementById('clue-banner');

  // Build cell lookup
  var cells = document.querySelectorAll('.cell[data-r]');
  var cellMap = {{}};
  cells.forEach(function(el) {{
    cellMap[el.dataset.r + ',' + el.dataset.c] = el;
  }});

  // Persist cell values to localStorage
  function saveState() {{
    var state = {{}};
    cells.forEach(function(el) {{
      var inp = el.querySelector('input');
      if (inp && inp.value) {{
        state[el.dataset.r + ',' + el.dataset.c] = inp.value;
      }}
    }});
    try {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }} catch(e) {{}}
  }}

  function loadState() {{
    try {{
      var state = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (!state) return;
      for (var key in state) {{
        var el = cellMap[key];
        if (el) {{
          var inp = el.querySelector('input');
          if (inp) inp.value = state[key];
        }}
      }}
    }} catch(e) {{}}
  }}

  // Find the across/down clue number for a given cell
  function findClueForCell(r, c) {{
    var result = [];
    for (var cc = c; cc >= 0; cc--) {{
      var el = cellMap[r + ',' + cc];
      if (!el) break;
      if (el.dataset.num && CLUES.across[el.dataset.num]) {{
        result.push({{dir: 'Across', num: el.dataset.num, text: CLUES.across[el.dataset.num]}});
        break;
      }}
    }}
    for (var rr = r; rr >= 0; rr--) {{
      var el = cellMap[rr + ',' + c];
      if (!el) break;
      if (el.dataset.num && CLUES.down[el.dataset.num]) {{
        result.push({{dir: 'Down', num: el.dataset.num, text: CLUES.down[el.dataset.num]}});
        break;
      }}
    }}
    return result;
  }}

  function showClue(r, c) {{
    var clues = findClueForCell(r, c);
    if (clues.length > 0) {{
      var html = clues.map(function(cl) {{
        return '<span class="clue-dir">' + cl.num + ' ' + cl.dir + ':</span> ' + cl.text;
      }}).join('<br>');
      banner.innerHTML = html;
      banner.className = 'visible';
    }}
  }}

  // Auto-advance, clue display, and save on input
  document.querySelectorAll('.cell input').forEach(function(inp) {{
    inp.addEventListener('input', function() {{
      if (this.value.length >= 1) {{
        this.value = this.value.slice(-1).toUpperCase();
        var all = Array.from(document.querySelectorAll('.cell input'));
        var idx = all.indexOf(this);
        if (idx >= 0 && idx < all.length - 1) {{
          all[idx + 1].focus();
        }}
      }}
      saveState();
    }});
    inp.addEventListener('focus', function() {{
      this.select();
      var cell = this.parentElement;
      if (cell.dataset.r !== undefined) {{
        showClue(parseInt(cell.dataset.r), parseInt(cell.dataset.c));
      }}
    }});
  }});

  // Restore saved state on load
  loadState();
}})();
</script>

</body>
</html>"""

    return html


def build_grid_html(grid: list[list[dict]], num_rows: int, num_cols: int) -> str:
    """Build the HTML grid using table layout for e-reader compatibility."""
    rows_html = []
    for r in range(num_rows):
        cells = []
        for c in range(num_cols):
            cell = grid[r][c]
            if cell["type"] == "black":
                cells.append('<div class="cell black"></div>')
            else:
                num_span = ""
                num_attr = ""
                if cell["number"]:
                    num_span = f'<span class="n">{cell["number"]}</span>'
                    num_attr = f' data-num="{cell["number"]}"'
                cells.append(
                    f'<div class="cell" data-r="{r}" data-c="{c}"{num_attr}>{num_span}'
                    f'<input type="text" maxlength="1" autocomplete="off" '
                    f'aria-label="{cell["number"] or ""}">'
                    f'</div>'
                )
        rows_html.append('<div class="grid-row">\n' + "\n".join(cells) + "\n</div>")

    return '<div class="grid">\n' + "\n".join(rows_html) + "\n</div>"


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

    if args.output:
        output_path = args.output
    else:
        stem = Path(path).stem
        output_dir = Path(path).parent.parent / "kindle"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{stem}.html")

    # Copy source photos to output directory and collect filenames for links
    photo_filenames = None
    source_photos = meta.get("source_photos", [])
    if source_photos:
        photo_filenames = []
        puzzle_dir = Path(path).parent.parent
        out_dir = Path(output_path).parent
        for photo_path in source_photos:
            src = puzzle_dir / photo_path
            if src.exists():
                dst = out_dir / src.name
                shutil.copy2(str(src), str(dst))
                photo_filenames.append(src.name)
                print(f"  Copied source photo: {src.name}")
            else:
                print(f"  Warning: source photo not found: {src}")

    html = generate_html(puzzle, grid, photo_filenames)

    with open(output_path, "w") as f:
        f.write(html)
    print(f"\nKindle HTML saved to: {output_path}")

    # Regenerate index.html with all puzzles
    generate_index(Path(output_path).parent, Path(path).parent)


def generate_index(kindle_dir: Path, puzzles_dir: Path):
    """Generate index.html listing all puzzles, sorted by date descending."""
    from datetime import datetime

    entries = []
    for puzzle_path in sorted(puzzles_dir.glob("crossword_*.json"), reverse=True):
        with open(puzzle_path) as f:
            data = json.load(f)
        meta = data["metadata"]
        date = meta.get("date", "")
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            date_display = dt.strftime("%A, %B %-d, %Y")
        except Exception:
            date_display = date
        rows = meta.get("grid_rows", meta["grid_size"])
        cols = meta.get("grid_cols", meta["grid_size"])
        entries.append({
            "file": puzzle_path.stem + ".html",
            "date": date_display,
            "author": meta.get("author", "Unknown"),
            "size": f"{rows}x{cols}",
        })

    items_html = ""
    for e in entries:
        items_html += (
            f'  <li><a href="{e["file"]}">'
            f'<div class="date">{e["date"]}</div>'
            f'<div class="meta">By {e["author"]} &mdash; {e["size"]}</div>'
            f'</a></li>\n'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Crosswords</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    background: #fff;
    color: #000;
    max-width: 800px;
    margin: 0 auto;
    padding: 24px 20px;
    -webkit-text-size-adjust: none;
  }}
  h1 {{
    font-size: 28px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
    text-align: center;
    border-bottom: 3px solid #000;
    padding-bottom: 10px;
    margin-bottom: 20px;
  }}
  .puzzle-list {{ list-style: none; padding: 0; }}
  .puzzle-list li {{ border-bottom: 1px solid #ccc; padding: 12px 0; }}
  .puzzle-list a {{ text-decoration: none; color: #000; display: block; }}
  .puzzle-list .date {{ font-size: 20px; font-weight: bold; }}
  .puzzle-list .meta {{ font-size: 14px; color: #444; margin-top: 2px; }}
</style>
</head>
<body>
<h1>Daily Crosswords</h1>
<ul class="puzzle-list">
{items_html}</ul>
</body>
</html>"""

    index_path = kindle_dir / "index.html"
    with open(index_path, "w") as f:
        f.write(html)
    print(f"Index saved to: {index_path}")


if __name__ == "__main__":
    main()
