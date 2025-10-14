import pandas as pd, os, requests
from collections import defaultdict
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment
from datetime import datetime
from io import BytesIO

# --- Load past boxes from GitHub Excel ---
excel_url = "https://github.com/apiusage/sg-4d-json/raw/main/4d_box_output.xlsx"
resp = requests.get(excel_url)
resp.raise_for_status()
df = pd.read_excel(BytesIO(resp.content))
col_values = df.iloc[:, 1].dropna().tolist()

# --- Flatten boxes into digits ---
boxes = []
for box in col_values:
    digits = [int(d) for d in ''.join(filter(str.isdigit, str(box)))]
    if digits:
        boxes.append(digits)

print(f"Total past boxes read: {len(boxes)}")

# --- Compute position-wise frequencies ---
position_counts = [defaultdict(int) for _ in range(16)]
for box in boxes:
    for i, digit in enumerate(box[:16]):
        position_counts[i][digit] += 1

position_probs = []
for pos_dict in position_counts:
    total = sum(pos_dict.values())
    probs = {digit: count/total for digit, count in pos_dict.items()} if total > 0 else {}
    position_probs.append(probs)

# --- Deterministic digit selection ---
def select_digit(prob_dict, exclude_row, exclude_col, digit_column_count):
    available = {d: p for d, p in prob_dict.items()
                 if d not in exclude_row and d not in exclude_col and digit_column_count.get(d, 0) < 2}
    if not available:
        choices = [d for d in range(10) if d not in exclude_row and d not in exclude_col and digit_column_count.get(d, 0) < 2]
        return choices[0] if choices else 0
    return max(available, key=available.get)

# --- Generate deterministic 4x4 box ---
def generate_box():
    box = [[-1] * 4 for _ in range(4)]
    col_digits_list = [[] for _ in range(4)]
    digit_column_count = {}

    for r in range(4):
        for c in range(4):
            pos = r * 4 + c
            exclude_row = box[r]
            exclude_col = col_digits_list[c]
            digit = select_digit(position_probs[pos], exclude_row, exclude_col, digit_column_count)
            box[r][c] = digit
            col_digits_list[c].append(digit)
            cols_with_digit = [i for i, col in enumerate(col_digits_list) if digit in col]
            digit_column_count[digit] = len(cols_with_digit)

    # ensure all digits 0-9 appear at least once
    flat_box = [d for row in box for d in row]
    missing_digits = [d for d in range(10) if d not in flat_box]
    for d in missing_digits:
        for r in range(4):
            for c in range(4):
                current_digit = box[r][c]
                if flat_box.count(current_digit) > 1 and digit_column_count.get(d, 0) < 2:
                    col_digits_list[c].remove(current_digit)
                    box[r][c] = d
                    col_digits_list[c].append(d)
                    flat_box = [x for row in box for x in row]
                    digit_column_count[d] = len([i for i, col in enumerate(col_digits_list) if d in col])
                    break
            if d in flat_box:
                break

    return box

# --- Generate box ---
predicted_box = generate_box()
print("Predicted 4x4 Box (unique columns, max 2 columns per digit):")
for row in predicted_box:
    print('  '.join(str(d) for d in row))  # <-- 2 spaces per digit

# --- Prepare string for Excel (2 spaces per digit) ---
box_str = '\n'.join('  '.join(str(d) for d in row) for row in predicted_box)
date_str = datetime.today().strftime("%d/%m/%Y (%a)")

# --- Save to Excel ---
fn = "4d_box_output.xlsx"
sheet_name = "Predicted_Box"
wb = load_workbook(fn) if os.path.exists(fn) else Workbook()
ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.create_sheet(sheet_name)

# Insert new row at top
ws.insert_rows(2)
if ws.max_row == 1:
    ws['A1'], ws['B1'], ws['C1'] = "Date", "4x4 Box", "Stats"

ws['A2'], ws['B2'] = date_str, box_str
ws['B2'].alignment = Alignment(wrapText=True)
ws.column_dimensions['B'].width = 25

wb.save(fn)
print(f"✅ 4x4 box generated and saved to '{fn}' in sheet '{sheet_name}'.")
