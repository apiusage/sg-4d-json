import requests
import pandas as pd
from datetime import datetime
import os

# JSON URL
url = "https://raw.githubusercontent.com/apiusage/sg-4d-json/main/4d.json"

# Fetch data
response = requests.get(url)
numbers = response.json()

# Take first 3 numbers
first, second, third = numbers[:3]

# Today's date (Singapore Time) — formatted M/D/YYYY
today = datetime.now().strftime('%-m/%-d/%Y')  # Use %-m only on Unix. If on Windows, change to %#m

# Day of the week
day_of_week = datetime.now().strftime('%a')  # 'Sat', 'Sun', etc.

# Year
year = datetime.now().year

# Create new row
new_row = {
    "DrawDate": today,
    "1st": first,
    "2nd": second,
    "3rd": third,
    "Days": day_of_week,
    "Not Used": "",  # Optional, keep empty
    "Year": year
}

file_path = "4d_results.csv"

# Read or create file
if os.path.exists(file_path):
    existing_df = pd.read_csv(file_path)

    # Append only if today not already present
    if not (existing_df["DrawDate"] == today).any():
        updated_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        updated_df = existing_df
else:
    updated_df = pd.DataFrame([new_row])

# Save back to CSV
updated_df.to_csv(file_path, index=False)
