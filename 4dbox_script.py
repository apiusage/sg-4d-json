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

    def generate_perms(box_digits: List[str]) -> List[str]:
        perms = list(itertools.permutations(range(4)))  # all 24 permutations
        res = []
        for i, j, k, l in itertools.product(range(0,16,4), range(1,16,4), range(2,16,4), range(3,16,4)):
            if max(i,j,k,l) < 16:
                g = [box_digits[i], box_digits[j], box_digits[k], box_digits[l]]
                res += [''.join(g[idx] for idx in p) for p in perms]
        return res

    def generate_box(numbers: List[str]) -> List[List[str]]:
        numbers = [str(n).zfill(4) for n in numbers]
        counters = [Counter() for _ in range(4)]
        for num in numbers:
            for i, d in enumerate(num):
                counters[i][d] += 1

        tops = [[d for d,_ in c.most_common(4)] for c in counters]
        box = [[tops[col][row] for col in range(4)] for row in range(4)]
        flat = [d for row in box for d in row]

        # Fill missing digits
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

    try:
        numbers = requests.get(
            "https://raw.githubusercontent.com/apiusage/sg-4d-json/refs/heads/main/4d.json",
            timeout=10
        ).json()
    except:
        numbers = []

    box = generate_box(numbers)
    print("Generated 4x4 Box:")
    print('\n'.join(' '.join(row) for row in box))

    flat_box = [d for row in box for d in row]
    perms = generate_perms(flat_box)
    dedup = len(set(''.join(sorted(p)) for p in perms))
    unique = len(set(perms))
    matched = [n for n in numbers if n in perms]

    date_str = datetime.today().strftime("%d/%m/%Y (%a)")

    wb = load_workbook(file_name) if os.path.exists(file_name) else Workbook()
    ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.create_sheet(sheet_name)
    ws.insert_rows(2)
    ws.cell(2, 1, date_str)  # column A: date (default font)
    ws.cell(2, 2, '\n'.join(' '.join(row) for row in box))  # column B: box (Courier New)
    ws.cell(2, 3, f"✅ Direct: {len(matched)}/{unique} ({len(matched)/unique*100:.2f}%)\n"
                    f"✅ iBet: {len(matched)}/{dedup} ({len(matched)/dedup*100:.2f}%)")  # column C: default font
    ws.cell(2, 2).alignment = ws.cell(2, 3).alignment = Alignment(wrapText=True)
    ws.cell(2, 2).font = Font(name="Courier New")  # only column B

    autofit_columns(ws)
    autofit_rows(ws)

    wb.save(file_name)
    print(f"✅ 4D box inserted at row 2 of '{sheet_name}' in '{file_name}'")

# ------------------- Function 2: Update stats for predicted boxes -------------------
def update_4d_box_stats(file_name="4d_box_output.xlsx", sheet_name="Predicted_Box"):
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
        flat = [d for d in b if d.isdigit()]
        perms = []
        for i,j,k,l in itertools.product(range(0,16,4), range(1,16,4), range(2,16,4), range(3,16,4)):
            if max(i,j,k,l)<16:
                g = [flat[i], flat[j], flat[k], flat[l]]
                perms += [''.join(p) for p in itertools.permutations(g)]
        dedup = len(set(''.join(sorted(p)) for p in perms))
        unique = len(set(perms))
        direct = sum(1 for n in past if n in perms)
        ibet = len({n for n in past if ''.join(sorted(n)) in {''.join(sorted(p)) for p in perms}})

        s.value = (f"▶ iBet: {ibet}/{dedup} ({ibet/dedup*100:.2f}%)\n"
                   f"▶ Direct: {direct}/{unique} ({direct/unique*100:.2f}%)\n"
                   f"▶ Total Sets hit: {direct}")
        s.alignment = Alignment(wrapText=True)
        # column C default font

    autofit_columns(ws)
    autofit_rows(ws)
    wb.save(file_name)
    print(f"✅ Stats updated in column C of '{file_name}'")

# ------------------- Function 3: Generate predicted box -------------------
def generate_predicted_box_from_github():
    LOCAL = "4d_box_output.xlsx"
    SHEET = "Perfect_4DBox"
    OUT = "Predicted_Box"
    URL = "https://github.com/apiusage/sg-4d-json/raw/main/4d_box_output.xlsx"

    if os.path.exists(LOCAL):
        df = pd.read_excel(LOCAL, sheet_name=SHEET)
    else:
        resp = requests.get(URL, timeout=10)
        resp.raise_for_status()
        xls = pd.ExcelFile(BytesIO(resp.content))
        if SHEET not in xls.sheet_names:
            return
        df = pd.read_excel(BytesIO(resp.content), sheet_name=SHEET)

    col = df.iloc[:,1].dropna().tolist()
    boxes = []
    for b in col:
        digits = [int(d) for d in ''.join(filter(str.isdigit, str(b)))]
        if digits:
            boxes.append(digits)

    pos_counts = [defaultdict(int) for _ in range(16)]
    for box in boxes:
        for i,d in enumerate(box[:16]):
            pos_counts[i][d]+=1
    pos_probs = [{d:c/sum(pos.values()) for d,c in pos.items()} if sum(pos.values())>0 else {} for pos in pos_counts]

    def select_digit(p,r,c,col_count):
        avail = {d:v for d,v in p.items() if d not in r and d not in c and col_count.get(d,0)<2}
        if avail: return max(avail,key=avail.get)
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

    print("Predicted 4x4 Box:")
    for row in box:
        print(' '.join(str(x) for x in row))

    box_str = '\n'.join(' '.join(str(x) for x in row) for row in box)
    date_str = datetime.today().strftime("%d/%m/%Y (%a)")
    wb = load_workbook(LOCAL) if os.path.exists(LOCAL) else Workbook()
    ws = wb[OUT] if OUT in wb.sheetnames else wb.create_sheet(OUT)
    ws.insert_rows(2)
    ws['A2'] = date_str  # default font
    ws['B2'] = box_str   # Courier New
    ws['B2'].alignment = Alignment(wrapText=True, vertical="top")
    ws['B2'].font = Font(name="Courier New")

    autofit_columns(ws)
    autofit_rows(ws)

    wb.save(LOCAL)
    print(f"✅ Predicted 4x4 box saved to '{LOCAL}' in '{OUT}' (columns auto-fitted)")

# ------------------- Autofit helpers -------------------
def autofit_columns(ws, max_width=120, padding=4, scale=1.3):
    """Auto-fit columns for wrapped text, default font."""
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            if cell.value is None:
                continue
            for line in str(cell.value).splitlines():
                max_len = max(max_len, len(line))
        # Column A (date) reasonable width
        if col_letter == 'A':
            ws.column_dimensions[col_letter].width = min(max(max_len + 2, 12), 20)
        else:
            ws.column_dimensions[col_letter].width = min((max_len + padding) * scale, max_width)

def autofit_rows(ws, default_row_height=15, approx_char_width=1.0, scale=1.0):
    """Auto-fit rows based on wrapped lines, default font."""
    col_widths = {i: ws.column_dimensions[get_column_letter(i)].width or 8.43 for i in range(1, ws.max_column+1)}
    for r in range(1, ws.max_row+1):
        max_lines = 1
        for c in range(1, ws.max_column+1):
            cell = ws.cell(row=r, column=c)
            if cell.value is None:
                continue
            col_w = col_widths[c]
            chars_per_line = max(1, int(col_w / approx_char_width))
            wrapped_lines = sum(ceil(len(l)/chars_per_line) for l in str(cell.value).splitlines())
            max_lines = max(max_lines, wrapped_lines)
        ws.row_dimensions[r].height = max_lines * default_row_height

# ------------------- Main -------------------
if __name__=="__main__":
    run_4d_box()
    update_4d_box_stats()
    generate_predicted_box_from_github()
