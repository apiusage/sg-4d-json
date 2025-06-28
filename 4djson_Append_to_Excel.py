import requests
import pandas as pd
import cheerio from 'cheerio';
from datetime import datetime
import os

url = "https://raw.githubusercontent.com/apiusage/sg-4d-json/main/4d.json"
response = requests.get(url)
numbers = response.json()

first, second, third = numbers[:3]

now = datetime.now()
today = f"{now.day}/{now.month}/{now.year}"

# Get digits used in all 3 numbers
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

file_path = "4d_results.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)

    if not (df["DrawDate"] == today).any():
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
else:
    df = pd.DataFrame([new_row])

df.to_csv(file_path, index=False)
print("Appended 4D results:", new_row)
