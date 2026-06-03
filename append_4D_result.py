import os
import csv
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# -------------------------
# CONFIG
# -------------------------
JSON_URL = "https://raw.githubusercontent.com/apiusage/sg-4d-json/main/4d.json"
CSV_FILE = "4d_history_results.csv"
SGT = ZoneInfo("Asia/Singapore")
HEADERS = ["DrawDate", "Day", "1st", "2nd", "3rd", "Starter", "Consolation"]
SEP = "|"

# -------------------------
# FETCH NUMBERS
# -------------------------
def fetch_nums():
    r = requests.get(JSON_URL, timeout=10)
    r.raise_for_status()
    nums = r.json()
    return [str(n).zfill(4) for n in nums]

# -------------------------
# INIT CSV IF NOT EXISTS
# -------------------------
def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HEADERS)
        print(f"📄 Created: {CSV_FILE}")

# -------------------------
# FETCH AND SAVE
# -------------------------
def fetch_and_save():
    try:
        nums = fetch_nums()

        if not nums or len(nums) < 23:
            print(f"❌ Insufficient data: got {len(nums)} numbers, need 23")
            return

        now = datetime.now(SGT)
        draw_date = f"{now.day}/{now.month}/{now.year}"
        day = now.strftime("%a")

        first       = nums[0]
        second      = nums[1]
        third       = nums[2]
        starter     = SEP.join(nums[3:13])   # 10 numbers
        consolation = SEP.join(nums[13:23])  # 10 numbers

        # Init file if needed
        init_csv()

        # Duplicate check
        with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
            existing_dates = [row[0] for row in csv.reader(f) if row]

        if draw_date in existing_dates:
            print(f"⚠️  {draw_date} already exists, skipping.")
            return

        # Append row
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([draw_date, day, first, second, third, starter, consolation])

        print(f"✅ Saved {draw_date} ({day})")
        print(f"   1st: {first} | 2nd: {second} | 3rd: {third}")
        print(f"   Starter:     {starter}")
        print(f"   Consolation: {consolation}")

    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    fetch_and_save()