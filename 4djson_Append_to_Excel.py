import requests
import pandas as pd
from datetime import datetime
import os

url = "https://raw.githubusercontent.com/apiusage/sg-4d-json/main/4d.json"

response = requests.get(url)
numbers = response.json()

first, second, third = numbers[:3]

now = datetime.now()
today = now.strftime('%Y-%m-%d')  # ISO date

new_row = {
    "DrawDate": today,
    "1st": first,
    "2nd": second,
    "3rd": third,
    "Days": now.strftime('%a'),
    "Not Used": "",
    "Year": now.year
}

file_path = "4d_results.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)

    # Ensure date format consistent for comparison
    if not (df["DrawDate"] == today).any():
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
else:
    df = pd.DataFrame([new_row])

df.to_csv(file_path, index=False)
print("Appended 4D results:", new_row)
