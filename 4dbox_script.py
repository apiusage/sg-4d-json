import os, itertools, requests, pandas as pd
from collections import Counter, defaultdict
from typing import List
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from math import ceil
from datetime import datetime
from io import BytesIO

# ------------------- Function 1: Generate & insert 4D box -------------------
def run_4d_box(sheet_name="Perfect_4DBox", file_name="4d_box_output.xlsx"):
    """Fetch latest 4D numbers, generate a 4x4 box, calculate stats, and save to Excel."""

    # Generate all permutations for iBet calculation
    def generate_perms(box_digits: List[str]) -> List[str]:
        perms = list(itertools.permutations(range(4)))  # all 24 permutations
        res = []
        for i, j, k, l in itertools.product(range(0,16,4), range(1,16,4), range(2,16,4), range(3,16,4)):
            if max(i,j,k,l) < 16:
                g = [box_digits[i], box_digits[j], box_digits[k], box_digits[l]]
                res += [''.join(g[idx] for idx in p) for p in perms]
        return res

    # Generate 4x4 box based on most frequent digits by position
    def generate_box(numbers: List[str]) -> List[List[str]]:
        numbers = [str(n).zfill(4) for n in numbers]
        counters = [Counter() for _ in range(4)]
        for num in numbers:
            for i, d in enumerate(num):
                counters[i][d] += 1

        # Top 4 digits per column
        tops = [[d for d,_ in c.most_common(4)] for c in counters]

        # Create 4x4 box
        box = [[tops[col][row] for col in range(4)] for row in range(4)]
        flat = [d for row in box for d in row]

        # Fill missing digits to ensure 0-9 appear
        missing = sorted(set('0123456789') - set(flat))
        idx = 15
        for m in missing:
            while idx >= 0:
                r, c = divmod(idx, 4)
                if flat.count(box[r][c]) > 1:
                    box[r][c] = m
                    flat[idx] = m
                    break
                idx -= 1
        return box

    # Fetch latest 4D numbers
    try:
        numbers = requests.get(
            "https://raw.githubusercontent.com/apiusage/sg-4d-json/refs/heads/main/4d.json",
            timeout=10
        ).json()
    except:
        numbers = []

    # Generate box and print
    box = generate_box(numbers)
    print("Generated 4x4 Box:")
    print('\n'.join(' '.join(row) for row in box))

    # Calculate permutations and stats
    flat_box = [d for row in box for d in row]
    perms = generate_perms(flat_box)
    dedup = len(set(''.join(sorted(p)) for p in perms))
    unique = len(set(perms))
    matched = [n for n in numbers if n in perms]

    # Format date
    today = datetime.today()
    date_str = today.strftime("%d/%m/%Y (%a)")
    date_str = '/'.join(p.lstrip('0') if i < 2 else p for i, p in enumerate(date_str.split('/')))

    # Save to Excel
    if os.path.exists(file_name):
        wb = load_workbook(file_name)
    else:
        wb = Workbook()

    ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.create_sheet(sheet_name)
    ws.insert_rows(2)
    ws.cell(2, 1, date_str)
    ws.cell(2, 2, '\n'.join(' '.join(row) for row in box))
    ws.cell(2, 3, f"✅ Direct: {len(matched)}/{unique} ({len(matched)/unique*100:.2f}%)\n"
                    f"✅ iBet: {len(matched)}/{dedup} ({len(matched)/dedup*100:.2f}%)")
    ws.cell(2, 2).alignment = ws.cell(2, 3).alignment = Alignment(wrapText=True)
    ws.column_dimensions['A'].width = 16
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 30

    wb.save(file_name)
    print(f"✅ 4D box inserted at row 2 of '{sheet_name}' in '{file_name}'")


# ------------------- Function 2: Update stats for predicted boxes -------------------
def update_4d_box_stats(file_name="4d_box_output.xlsx", sheet_name="Predicted_Box"):
    """Update iBet/Direct stats for all predicted boxes in Excel."""
    try:
        past = [str(n).zfill(4) for n in requests.get(
            "https://raw.githubusercontent.com/apiusage/sg-4d-json/refs/heads/main/4d.json",
            timeout=10
        ).json()]
    except:
        past = []

    if not os.path.exists(file_name):
        return

    wb = load_workbook(file_name)
    if sheet_name not in wb.sheetnames:
        return

    ws = wb[sheet_name]

    for r in range(2, ws.max_row + 1):
        b = ws[f"B{r}"].value
        s = ws[f"C{r}"]
        if not b or s.value:
            continue

        # Flatten box digits
        flat = [d for d in b if d.isdigit()]

        # Generate all permutations
        perms = []
        for i, j, k, l in itertools.product(range(0,16,4), range(1,16,4), range(2,16,4), range(3,16,4)):
            if max(i,j,k,l) < 16:
                g = [flat[i], flat[j], flat[k], flat[l]]
                perms += [''.join(p) for p in itertools.permutations(g)]

        # Stats
        dedup = len(set(''.join(sorted(p)) for p in perms))
        unique = len(set(perms))
        direct = sum(1 for n in past if n in perms)
        ibet = len({n for n in past if ''.join(sorted(n)) in {''.join(sorted(p)) for p in perms}})

        s.value = (f"▶ iBet: {ibet}/{dedup} ({ibet/dedup*100:.2f}%)\n"
                   f"▶ Direct: {direct}/{unique} ({direct/unique*100:.2f}%)\n"
                   f"▶ Total Sets hit: {direct}")
        s.alignment = Alignment(wrapText=True)

    wb.save(file_name)
    print(f"✅ Stats updated in column C of '{file_name}'")


# ------------------- Function 3: Generate predicted box from GitHub/local -------------------
def generate_predicted_box_from_github():
    """Generate a new 4x4 predicted box from historical boxes (local or GitHub)."""
    LOCAL = "4d_box_output.xlsx"
    SHEET = "Perfect_4DBox"
    OUT = "Predicted_Box"
    URL = "https://github.com/apiusage/sg-4d-json/raw/main/4d_box_output.xlsx"

    # Load past boxes
    if os.path.exists(LOCAL):
        df = pd.read_excel(LOCAL, sheet_name=SHEET)
    else:
        resp = requests.get(URL, timeout=10)
        resp.raise_for_status()
        xls = pd.ExcelFile(BytesIO(resp.content))
        if SHEET not in xls.sheet_names:
            return
        df = pd.read_excel(BytesIO(resp.content), sheet_name=SHEET)

    # Flatten boxes into digits
    col = df.iloc[:, 1].dropna().tolist()
    boxes = []
    for b in col:
        digits = [int(d) for d in ''.join(filter(str.isdigit, str(b)))]
        if digits:
            boxes.append(digits)

    # Compute position-wise probabilities
    pos_counts = [defaultdict(int) for _ in range(16)]
    for box in boxes:
        for i, d in enumerate(box[:16]):
            pos_counts[i][d] += 1
    pos_probs = [{d:c/sum(pos.values()) for d,c in pos.items()} if sum(pos.values())>0 else {} for pos in pos_counts]

    # Deterministic box generation
    def select_digit(p, r, c, col_count):
        avail = {d:v for d,v in p.items() if d not in r and d not in c and col_count.get(d,0)<2}
        if avail:
            return max(avail, key=avail.get)
        choices = [d for d in range(10) if d not in r and d not in c and col_count.get(d,0)<2]
        return choices[0] if choices else 0

    box = [[-1]*4 for _ in range(4)]
    col_digits = [[] for _ in range(4)]
    col_count = {}
    for r in range(4):
        for c in range(4):
            d = select_digit(pos_probs[r*4+c], box[r], col_digits[c], col_count)
            box[r][c] = d
            col_digits[c].append(d)
            col_count[d] = sum(1 for col in col_digits if d in col)

    # Print predicted box
    print("Predicted 4x4 Box:")
    for row in box:
        print(' '.join(str(x) for x in row))

    # Save to Excel
    box_str = '\n'.join(' '.join(str(x) for x in row) for row in box)
    date_str = datetime.today().strftime("%d/%m/%Y (%a)")
    wb = load_workbook(LOCAL) if os.path.exists(LOCAL) else Workbook()
    ws = wb[OUT] if OUT in wb.sheetnames else wb.create_sheet(OUT)
    ws.insert_rows(2)
    ws['A2'] = date_str
    ws['B2'] = box_str
    ws['B2'].alignment = Alignment(wrapText=True, vertical="top")
    ws['B2'].font = Font(name="Courier New")

    # after writing cells and setting alignment/font
    autofit_columns(ws, max_width=60, padding=2, monospace=True)
    autofit_rows(ws, default_row_height=15, approx_char_width=1.0, monospace=True)

    wb.save(LOCAL)
    print(f"✅ Predicted 4x4 box saved to '{LOCAL}' in '{OUT}' (auto-fitted columns)")

def autofit_columns(ws, max_width=80, padding=2, monospace=True):
    """
    Approximate auto-fit for column widths.
    - ws: openpyxl worksheet
    - max_width: cap for column width
    - padding: extra characters to add as buffer
    - monospace: True if using a monospaced font (Courier New). If False, uses a small scale factor.
    """
    scale = 1.0 if monospace else 1.2  # proportional fonts need a scale factor
    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.value is None:
                continue
            text = str(cell.value)
            # measure by longest single line (handles newlines)
            for line in text.splitlines():
                length = len(line)
                if length > max_length:
                    max_length = length
        # compute width in Excel "char" units (approx)
        new_width = min((max_length + padding) * scale, max_width)
        # only set if we found something (avoid overwriting default small widths)
        if max_length > 0:
            ws.column_dimensions[col_letter].width = new_width

def autofit_rows(ws, default_row_height=15, approx_char_width=1.0, monospace=True):
    """
    Approximate row height based on wrapped lines.
    - ws: openpyxl worksheet
    - default_row_height: height in points per line (approx 15 is typical)
    - approx_char_width: number of "characters" that fit per Excel column width unit (approx 1 for monospace)
    - monospace: affects how we compute wrap length (if False we use a scale factor)
    """
    scale = 1.0 if monospace else 1.2
    # Pre-read current column widths (use openpyxl stored width or default)
    col_widths = {}
    for i in range(1, ws.max_column + 1):
        letter = get_column_letter(i)
        w = ws.column_dimensions[letter].width
        if w is None:
            # default excel column width approx 8.43 -> approximated here
            w = 8.43
        col_widths[i] = w

    for row_idx in range(1, ws.max_row + 1):
        max_lines = 1
        for col_idx in range(1, ws.max_column + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            if cell.value is None:
                continue
            text = str(cell.value)
            col_w = col_widths.get(col_idx, 8.43)
            # how many characters can fit per visual line (approx)
            chars_per_line = max(1, int(col_w / (approx_char_width * scale)))
            # calculate required lines accounting for existing '\n' and wrapping
            lines = 0
            for raw_line in text.splitlines():
                if len(raw_line) == 0:
                    lines += 1
                else:
                    lines += ceil(len(raw_line) / chars_per_line)
            if lines > max_lines:
                max_lines = lines
        # set row height (points) — adjust multiplier to taste
        ws.row_dimensions[row_idx].height = max_lines * default_row_height

# ------------------- Main -------------------
if __name__=="__main__":
    run_4d_box()
    update_4d_box_stats()
    generate_predicted_box_from_github()
