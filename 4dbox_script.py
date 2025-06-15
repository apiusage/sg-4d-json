from collections import Counter
from typing import List
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from datetime import datetime
import os
import itertools
import requests

def generate_permutations(box_digits: List[str], pool=16, num=4) -> List[str]:
    perms = list(itertools.permutations(range(num)))  # 24 permutations of 4 digits
    results = []

    for i in range(0, pool, num):
        for j in range(1, pool, num):
            for k in range(2, pool, num):
                for l in range(3, pool, num):
                    if max(i, j, k, l) < pool:
                        group = [box_digits[i], box_digits[j], box_digits[k], box_digits[l]]
                        for p in perms:
                            results.append(''.join(group[idx] for idx in p))
    return results

def generate_4d_box(numbers: List[str]) -> List[List[str]]:
    numbers = [str(num).zfill(4) for num in numbers]
    position_counters = [Counter() for _ in range(4)]

    for num in numbers:
        for i, digit in enumerate(num):
            position_counters[i][digit] += 1

    top_digits_by_position = [
        [digit for digit, _ in counter.most_common(4)]
        for counter in position_counters
    ]

    box = [
        [top_digits_by_position[col][row] for col in range(4)]
        for row in range(4)
    ]

    flat = [digit for row in box for digit in row]
    all_digits = set('0123456789')
    used_digits = set(flat)
    missing_digits = sorted(all_digits - used_digits)

    if missing_digits:
        replace_idx = 15
        for missing in missing_digits:
            while replace_idx >= 0:
                r, c = divmod(replace_idx, 4)
                current = box[r][c]
                if flat.count(current) > 1:
                    box[r][c] = missing
                    flat[replace_idx] = missing
                    break
                replace_idx -= 1

    return box

# Step 1: Fetch numbers from JSON
try:
    response = requests.get("https://raw.githubusercontent.com/apiusage/sg-4d-json/refs/heads/main/4d.json", timeout=10)
    response.raise_for_status()
    numbers = response.json()
except Exception as e:
    print(f"❌ Failed to fetch numbers: {e}")
    numbers = []

# Step 2: Generate box
box = generate_4d_box(numbers)
box_str = '\n'.join(' '.join(row) for row in box)
print(box_str)

flat_box = [digit for row in box for digit in row]
permutations = generate_permutations(flat_box)

# Step 3: iBet and Direct matching
dedup_count = len(set(''.join(sorted(p)) for p in permutations))
unique_permutations_count = len(set(permutations))
matched = [num for num in numbers if num in permutations]

# Step 4: Stats
direct_percent = len(matched) / unique_permutations_count * 100 if unique_permutations_count else 0
ibet_percent = len(matched) / dedup_count * 100 if dedup_count else 0
direct_string = f"✅ Direct: {len(matched)}/{unique_permutations_count} ({direct_percent:.2f}%)"
ibet_string = f"✅ iBet: {len(matched)}/{dedup_count} ({ibet_percent:.2f}%)"

# Step 5: Format date like 15/6/2025 (Sun)
today = datetime.today()
date_str = today.strftime("%d/%m/%Y (%a)")
date_str = '/'.join(part.lstrip('0') if i < 2 else part for i, part in enumerate(date_str.split('/')))

# Step 6: Excel setup
file_name = "4d_box_output.xlsx"
if os.path.exists(file_name):
    wb = load_workbook(file_name)
    ws = wb.active
else:
    wb = Workbook()
    ws = wb.active

# Step 7: Write to Excel
ws.insert_rows(2)
ws.cell(row=2, column=1, value=date_str)
ws.cell(row=2, column=2, value=box_str)
ws.cell(row=2, column=3, value=f"{direct_string}\n{ibet_string}")
ws.cell(row=2, column=2).alignment = Alignment(wrapText=True)
ws.cell(row=2, column=3).alignment = Alignment(wrapText=True)
ws.column_dimensions['A'].width = 16
ws.column_dimensions['B'].width = 20
ws.column_dimensions['C'].width = 30
ws.row_dimensions[2].height = None

# Step 8: Save
wb.save(file_name)
print(f"✅ 4D box inserted at row 2 of '{file_name}'")
