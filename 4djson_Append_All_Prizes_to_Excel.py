import os, random, pandas as pd
from collections import Counter, defaultdict
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, PatternFill, Font
from datetime import datetime
import math
import requests

# ---------------- CONFIG ----------------
CSV_FILE = "4d_results_all.xlsx"
PRED_FILE = "4d_box_output.xlsx"
RESULTS_SHEET = "Results"
PRED_SHEET = "Direct_Prediction"
TOP_N = 5
DECAY_HALF_LIFE_DAYS = 90.0
PRIZE_WEIGHTS = {"1st": 1.0, "2nd": 0.9, "3rd": 0.8, "Starter": 0.5, "Consolation": 0.3}
WEIGHTS = {"freq": 0.35, "pos": 0.3, "recency": 0.15, "balance": 0.1, "streak": 0.05, "rand": 0.05}
COLUMN_C_COLORS = ["CCFFFF", "CCFFCC", "FFCCCC", "FFFFCC"]  # pastel colors

# ---------------- FETCH & SAVE LATEST RESULTS ----------------
def fetch_and_save_results():
    url = "https://raw.githubusercontent.com/apiusage/sg-4d-json/main/4d.json"
    nums = requests.get(url).json()
    row = [
        datetime.now().strftime("%a (%Y-%m-%d)"),
        int(nums[0]), int(nums[1]), int(nums[2]),
        " ".join(nums[3:13]),
        " ".join(nums[13:23])
    ]
    headers = ["DrawDate","1st","2nd","3rd","Starter","Consolation"]

    if not os.path.exists(CSV_FILE):
        wb = Workbook()
        ws = wb.active
        ws.title = RESULTS_SHEET
        ws.append(headers)
        fill = PatternFill("solid", fgColor="FFFF00")
        for c in ws[1]: c.fill, c.font = fill, Font(bold=True)
        wb.save(CSV_FILE)

    wb = load_workbook(CSV_FILE)
    ws = wb[RESULTS_SHEET]

    dates = [cell.value for cell in ws["A"]]
    if row[0] in dates:
        print(f"⚠️ {row[0]} already exists in results.")
        return
    ws.append(row)
    wb.save(CSV_FILE)
    print(f"✅ Saved 4D results for {row[0]}.")

# ---------------- CALCULATE STATS ----------------
def calculate_stats(predicted_numbers):
    if not predicted_numbers:
        return "▶ iBet: 0/0 (0.00%)\n▶ Direct: 0/0 (0.00%)\n▶ Total Sets hit: 0"

    try:
        df = pd.read_excel(CSV_FILE)
    except:
        return "Error fetching past results."

    number_to_prize = {}
    for _, row in df.iterrows():
        for prize_col in ['1st','2nd','3rd']:
            if prize_col in row and not pd.isna(row[prize_col]):
                number_to_prize[str(row[prize_col]).zfill(4)] = prize_col
        for col in ['Starter','Consolation']:
            if col in row and not pd.isna(row[col]):
                for n in str(row[col]).split():
                    number_to_prize[n.zfill(4)] = col

    direct_hits, ibet_hits = [], []

    for num in predicted_numbers:
        if num in number_to_prize:
            direct_hits.append(f"{num} ({number_to_prize[num]})")
        for past_num in number_to_prize:
            if sorted(num) == sorted(past_num):
                ibet_hits.append(f"{num} ({number_to_prize[past_num]})")
                break

    n = len(predicted_numbers)
    direct_count = len(direct_hits)
    ibet_count = len(ibet_hits)
    direct_pct = (direct_count / n * 100) if n else 0
    ibet_pct = (ibet_count / n * 100) if n else 0

    return f"▶ iBet: {ibet_count}/{n} ({ibet_pct:.2f}%) - {', '.join(ibet_hits)}\n" \
           f"▶ Direct: {direct_count}/{n} ({direct_pct:.2f}%) - {', '.join(direct_hits)}\n" \
           f"▶ Total Sets hit: {direct_count}"

# ---------------- ENSURE HEADERS ----------------
def ensure_headers(ws):
    headers = ["Date", "Predicted 4D Numbers", "Stats"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        if not cell.value:
            cell.value = header
            cell.fill = PatternFill("solid", fgColor="FFFF00")
            cell.font = Font(bold=True)

# ---------------- CALCULATE STATS IN EXCEL ----------------
def calculate_stats_in_excel():
    if not os.path.exists(PRED_FILE):
        print("No prediction Excel file found.")
        return

    wb = load_workbook(PRED_FILE)
    ws = wb[PRED_SHEET] if PRED_SHEET in wb.sheetnames else wb.create_sheet(PRED_SHEET)
    ensure_headers(ws)

    if ws.max_row < 2:
        print("No previous predictions to calculate stats.")
        wb.save(PRED_FILE)
        return

    b_value = ws["B2"].value
    if not b_value or ws["C2"].value:
        print("No numbers found or stats already calculated.")
        wb.save(PRED_FILE)
        return

    predicted_numbers = b_value.split()
    stats_text = calculate_stats(predicted_numbers)
    ws["C2"].value = stats_text
    ws["C2"].alignment = Alignment(wrapText=True)

    # Determine color based on previous row
    last_row = 1
    for i in range(ws.max_row, 1, -1):
        if ws.cell(row=i, column=3).value:
            last_row = i
            break
    color_index = (last_row - 1) % len(COLUMN_C_COLORS)
    ws["C2"].fill = PatternFill("solid", fgColor=COLUMN_C_COLORS[color_index])
    ws["C2"].font = Font(bold=True)

    wb.save(PRED_FILE)
    print(f"✅ Stats calculated for previous prediction: {b_value}")

# ---------------- PREDICT NEW NUMBERS ----------------
def predict_and_append_excel():
    df = pd.read_excel(CSV_FILE)
    records = []
    for _, row in df.iterrows():
        try:
            date = pd.to_datetime(str(row['DrawDate']).split('(')[1].split(')')[0])
        except:
            date = pd.to_datetime(str(row['DrawDate']), errors='coerce')
        if pd.isna(date): continue
        for t in ['1st','2nd','3rd']:
            if t in row and not pd.isna(row[t]): records.append((date,t,str(row[t]).zfill(4)))
        for col in ['Starter','Consolation']:
            if col in row and not pd.isna(row[col]):
                records.extend((date,col,n.zfill(4)) for n in str(row[col]).split() if n)
    records.sort(key=lambda x: x[0])
    if not records: return []

    full_freq, pos_freq, recency, streaks = {}, [Counter() for _ in range(4)], defaultdict(float), defaultdict(int)
    today = records[-1][0]
    for idx, (date,t,num) in enumerate(records):
        w = PRIZE_WEIGHTS.get(t,0.5)
        full_freq[num] = full_freq.get(num,0)+w
        for p,d in enumerate(num): pos_freq[p][d]+=w
        recency[num]+= w*(0.5**((today-date).days/DECAY_HALF_LIFE_DAYS))
        if idx>0 and records[idx-1][2]==num: streaks[num]+=1

    norm = lambda d: {k:1.0 if max(d.values())==min(d.values()) else (v-min(d.values()))/(max(d.values())-min(d.values())) for k,v in d.items()}
    norm_full, norm_rec = norm(full_freq), norm(recency)
    max_streak = max(streaks.values()) if streaks else 1

    def digit_pos_score(num):
        s=1
        for p,d in enumerate(num): s*= pos_freq[p].get(d,0)/sum(pos_freq[p].values())
        return s

    def balance_score(num):
        digits = [int(d) for d in num]
        odd=sum(d%2 for d in digits)
        high=sum(1 for d in digits if d>=5)
        low=4-high
        return (1-abs(odd-(4-odd))/4+1-abs(high-low)/4)/2

    candidates=set(full_freq.keys())
    combos=[[d] for d,_ in pos_freq[0].most_common(5)]
    for p in range(1,4):
        combos=[c+[d] for c in combos for d,_ in pos_freq[p].most_common(5)]
    candidates.update(''.join(c) for c in combos)

    scores={}
    for num in candidates:
        f_full=norm_full.get(num,0)
        f_pos=math.log1p(digit_pos_score(num)) if digit_pos_score(num)>0 else 0
        f_rec=norm_rec.get(num,0)
        f_bal=balance_score(num)
        f_streak=streaks.get(num,0)/(1+max_streak)
        scores[num]= WEIGHTS["freq"]*f_full + WEIGHTS["pos"]*f_pos + WEIGHTS["recency"]*f_rec + WEIGHTS["balance"]*f_bal + WEIGHTS["streak"]*f_streak + WEIGHTS["rand"]*random.uniform(0,0.05)

    top_numbers = [num for num,_ in sorted(scores.items(), key=lambda x:x[1], reverse=True)[:TOP_N]]

    today_str = datetime.now().strftime("%a - %d/%m/%Y")
    wb = Workbook() if not os.path.exists(PRED_FILE) else load_workbook(PRED_FILE)
    ws = wb[PRED_SHEET] if PRED_SHEET in wb.sheetnames else wb.create_sheet(PRED_SHEET)
    ensure_headers(ws)

    ws.insert_rows(2)
    ws["A2"], ws["B2"] = today_str, ' '.join(top_numbers)
    ws["C2"].value = ""  # Column C empty for next round

    # Determine color based on previous row
    last_row = 1
    for i in range(ws.max_row, 1, -1):
        if ws.cell(row=i, column=3).value:
            last_row = i
            break
    color_index = (last_row - 1) % len(COLUMN_C_COLORS)
    ws["C2"].fill = PatternFill("solid", fgColor=COLUMN_C_COLORS[color_index])
    ws["C2"].font = Font(bold=True)

    # Adjust column widths
    for col in ws.columns:
        ws.column_dimensions[get_column_letter(col[0].column)].width = max(len(str(c.value)) if c.value else 0 for c in col)+2

    wb.save(PRED_FILE)
    print(f"✅ Prediction appended for {today_str} (Column C empty)")
    return top_numbers

# ---------------- MAIN ----------------
if __name__ == "__main__":
    fetch_and_save_results()
    calculate_stats_in_excel()
    predicted = predict_and_append_excel()
    print("Predicted 4D Numbers:", predicted)
