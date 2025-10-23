import os, random, itertools, math, requests, pandas as pd
from collections import Counter, defaultdict
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from math import ceil
from io import BytesIO

# ---------------- CONFIG ----------------
CSV_FILE = "4d_results.csv"
EXCEL_FILE = "4d_box_output.xlsx"
RESULTS_SHEET = "Results"
BOX_SHEET = "Perfect_4DBox"
PRED_SHEET = "Predicted_Box"
COLUMN_C_COLORS = ["CCFFFF", "CCFFCC", "FFCCCC", "FFFFCC"]  # pastel colors for stats column

# ---------------- FETCH & SAVE LATEST RESULTS ----------------
def fetch_and_save_results():
    url = "https://raw.githubusercontent.com/apiusage/sg-4d-json/main/4d.json"
    try:
        numbers = requests.get(url).json()
    except:
        print("⚠️ Failed to fetch 4D numbers")
        return []

    first, second, third = numbers[:3]
    now = datetime.now()
    today = f"{now.day}/{now.month}/{now.year}"

    # unused digits
    used_digits = set(str(first) + str(second) + str(third))
    all_digits = set("0123456789")
    not_used_digits = sorted(all_digits - used_digits)
    not_used_str = "_".join(not_used_digits) + "_" if not_used_digits else ""

    new_row = {
        "DrawDate": today,
        "1st": first,
        "2nd": second,
        "3rd": third,
        "Days": now.strftime('%a'),
        "Not Used": not_used_str,
        "Year": now.year
    }

    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        if not (df["DrawDate"] == today).any():
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])

    df.to_csv(CSV_FILE, index=False)
    print("✅ Appended 4D results:", new_row)
    return numbers

# ---------------- 4D BOX GENERATION ----------------
def run_4d_box(sheet_name=BOX_SHEET, file_name=EXCEL_FILE, numbers=None):
    if not numbers:
        try:
            numbers = requests.get("https://raw.githubusercontent.com/apiusage/sg-4d-json/main/4d.json").json()
        except:
            numbers = []

    numbers = [str(n).zfill(4) for n in numbers]

    # build 4x4 box
    counters = [Counter() for _ in range(4)]
    for num in numbers:
        for i, d in enumerate(num):
            counters[i][d] += 1

    tops = [[d for d,_ in c.most_common(4)] for c in counters]
    box = [[tops[col][row] for col in range(4)] for row in range(4)]
    flat = [d for row in box for d in row]

    missing = sorted(set('0123456789') - set(flat))
    idx = 15
    for m in missing:
        while idx >= 0:
            r,c = divmod(idx, 4)
            if flat.count(box[r][c]) > 1:
                box[r][c] = m
                flat[idx] = m
                break
            idx -=1

    print("Generated 4x4 Box:")
    for row in box:
        print(' '.join(row))

    # calculate permutations for stats
    perms = list(itertools.permutations(flat))
    dedup = len(set(''.join(sorted(p)) for p in perms))
    unique = len(set(perms))
    matched = [n for n in numbers if n in [''.join(p) for p in perms]]

    # save to Excel
    wb = load_workbook(file_name) if os.path.exists(file_name) else Workbook()
    ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.create_sheet(sheet_name)
    ws.insert_rows(2)
    date_str = datetime.today().strftime("%d/%m/%Y (%a)")
    ws.cell(2,1,date_str)
    ws.cell(2,2,'\n'.join(' '.join(row) for row in box))
    ws.cell(2,3,f"✅ Direct: {len(matched)}/{unique} ({len(matched)/unique*100:.2f}%)\n"
                  f"✅ iBet: {len(matched)}/{dedup} ({len(matched)/dedup*100:.2f}%)")
    ws.cell(2,2).alignment = ws.cell(2,3).alignment = Alignment(wrapText=True)
    ws.cell(2,2).font = Font(name="Courier New")

    autofit_columns(ws)
    autofit_rows(ws)
    wb.save(file_name)
    print(f"✅ 4D box inserted at row 2 in '{file_name}'")

# ---------------- UPDATE BOX STATS ----------------
def update_4d_box_stats(file_name=EXCEL_FILE, sheet_name=PRED_SHEET):
    try:
        past = [str(n).zfill(4) for n in requests.get(
            "https://raw.githubusercontent.com/apiusage/sg-4d-json/main/4d.json").json()]
    except:
        past = []

    if not os.path.exists(file_name):
        return
    wb = load_workbook(file_name)
    if sheet_name not in wb.sheetnames:
        return
    ws = wb[sheet_name]

    for r in range(2, ws.max_row+1):
        b = ws[f"B{r}"].value
        s = ws[f"C{r}"]
        if not b or s.value:
            continue
        flat = [d for d in b if d.isdigit()]
        perms = []
        for i,j,k,l in itertools.product(range(0,16,4), range(1,16,4), range(2,16,4), range(3,16,4)):
            if max(i,j,k,l)<16:
                g=[flat[i],flat[j],flat[k],flat[l]]
                perms += [''.join(p) for p in itertools.permutations(g)]
        dedup = len(set(''.join(sorted(p)) for p in perms))
        unique = len(set(perms))
        direct = sum(1 for n in past if n in perms)
        ibet = len({n for n in past if ''.join(sorted(n)) in {''.join(sorted(p)) for p in perms}})

        s.value = (f"▶ iBet: {ibet}/{dedup} ({ibet/dedup*100:.2f}%)\n"
                   f"▶ Direct: {direct}/{unique} ({direct/unique*100:.2f}%)\n"
                   f"▶ Total Sets hit: {direct}")
        s.alignment = Alignment(wrapText=True)

    autofit_columns(ws)
    autofit_rows(ws)
    wb.save(file_name)
    print(f"✅ Stats updated in '{file_name}'")

# ---------------- PREDICT BOX ----------------
def generate_predicted_box():
    LOCAL = EXCEL_FILE
    SHEET = BOX_SHEET
    OUT = PRED_SHEET

    if os.path.exists(LOCAL):
        df = pd.read_excel(LOCAL, sheet_name=SHEET)
    else:
        return

    col = df.iloc[:,1].dropna().tolist()
    boxes = []
    for b in col:
        digits = [int(d) for d in ''.join(filter(str.isdigit,str(b)))]
        if digits: boxes.append(digits)

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
    ws['A2'] = date_str
    ws['B2'] = box_str
    ws['B2'].alignment = Alignment(wrapText=True, vertical="top")
    ws['B2'].font = Font(name="Courier New")
    autofit_columns(ws)
    autofit_rows(ws)
    wb.save(LOCAL)
    print(f"✅ Predicted 4x4 box saved to '{LOCAL}' in '{OUT}'")

# ---------------- AUTOFIT HELPERS ----------------
def autofit_columns(ws, max_width=120, padding=4, scale=1.3):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            if cell.value is None: continue
            for line in str(cell.value).splitlines():
                max_len = max(max_len, len(line))
        ws.column_dimensions[col_letter].width = min((max_len+padding)*scale, max_width)

def autofit_rows(ws, default_row_height=15, approx_char_width=1.0, scale=1.0):
    col_widths = {i: ws.column_dimensions[get_column_letter(i)].width or 8.43 for i in range(1, ws.max_column+1)}
    for r in range(1, ws.max_row+1):
        max_lines = 1
        for c in range(1, ws.max_column+1):
            cell = ws.cell(row=r, column=c)
            if cell.value is None: continue
            col_w = col_widths[c]
            chars_per_line = max(1,int(col_w/approx_char_width))
            wrapped_lines = sum(ceil(len(l)/chars_per_line) for l in str(cell.value).splitlines())
            max_lines = max(max_lines, wrapped_lines)
        ws.row_dimensions[r].height = max_lines * default_row_height

# ---------------- MAIN ----------------
if __name__=="__main__":
    numbers = fetch_and_save_results()
    run_4d_box(numbers=numbers)
    update_4d_box_stats()
    generate_predicted_box()
