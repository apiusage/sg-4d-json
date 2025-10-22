import requests
import pandas as pd
from datetime import datetime
import os

# --- Fetch data ---
url = "https://raw.githubusercontent.com/apiusage/sg-4d-json/main/4d.json"
response = requests.get(url)
numbers = response.json()

# --- Assign prizes ---
first, second, third = numbers[:3]
starter = numbers[3:13]        # next 10
consolation = numbers[13:23]   # next 10

# --- Time info ---
now = datetime.now()
draw_date_str = now.strftime("%a (%Y-%m-%d)")  # e.g. Wed (2025-10-22)

# --- New row ---
new_row = {
    "DrawDate": draw_date_str,
    "1st": first,
    "2nd": second,
    "3rd": third,
    "Starter": " ".join(starter),
    "Consolation": " ".join(consolation),
}

# --- Save to CSV ---
file_path = "4d_results_all.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)

    # ✅ Avoid duplicate entry for same DrawDate
    if (df["DrawDate"] == draw_date_str).any():
        print(f"⚠️ Results for {draw_date_str} already exist, skipping append.")
    else:
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(file_path, index=False)
        print(f"✅ Appended new 4D results for {draw_date_str}.")
else:
    df = pd.DataFrame([new_row])
    df.to_csv(file_path, index=False)
    print(f"✅ Created new CSV and added first record for {draw_date_str}.")
