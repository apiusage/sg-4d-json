import pandas as pd, os, requests, itertools
from openpyxl import load_workbook
from openpyxl.styles import Alignment
from io import BytesIO

# --- Load past winning numbers from GitHub ---
try:
    past_numbers = [str(n).zfill(4) for n in requests.get(
        "https://raw.githubusercontent.com/apiusage/sg-4d-json/refs/heads/main/4d.json", timeout=10
    ).json()]
except Exception as e:
    print(f"❌ Failed to fetch past numbers: {e}")
    past_numbers = []

# --- Load predicted boxes from Excel ---
fn = "4d_box_output.xlsx"
sheet_name = "Predicted_Box"
wb = load_workbook(fn)
ws = wb[sheet_name]

# Skip header
for row_idx in range(2, ws.max_row+1):
    box_cell = ws[f"B{row_idx}"]
    if not box_cell.value:
        continue

    # Flatten the 4x4 box into digits
    flat_box = [d for d in box_cell.value if d.isdigit()]

    # --- Generate all iBet permutations ---
    perms = []
    for i, j, k, l in itertools.product(range(0,16,4), range(1,16,4), range(2,16,4), range(3,16,4)):
        if max(i,j,k,l) < 16:
            group = [flat_box[i], flat_box[j], flat_box[k], flat_box[l]]
            perms += [''.join(p) for p in itertools.permutations(group)]

    # --- Stats ---
    dedup_count = len(set(''.join(sorted(p)) for p in perms))  # for iBet
    unique_count = len(set(perms))  # for Direct
    direct_hits = sum(1 for n in past_numbers if n in perms)
    ibet_hits = len(set(n for n in past_numbers if ''.join(sorted(n)) in set(''.join(sorted(p)) for p in perms)))

    ibet_percent = ibet_hits/dedup_count*100 if dedup_count else 0
    direct_percent = direct_hits/unique_count*100 if unique_count else 0

    # --- Format stats ---
    stats_str = (
        f"▶ iBet Winning rate: {ibet_hits}/{dedup_count} ({ibet_percent:.2f}%)\n"
        f"▶ Direct Winning rate: {direct_hits}/{unique_count} ({direct_percent:.2f}%)\n"
        f"▶ Total Sets hit: {direct_hits}"
    )

    # Write to column C
    ws[f"C{row_idx}"] = stats_str
    ws[f"C{row_idx}"].alignment = Alignment(wrapText=True)

# --- Save Excel ---
wb.save(fn)
print(f"✅ Stats updated in column C of '{fn}'")
