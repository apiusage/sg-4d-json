import requests
import pandas as pd
from datetime import datetime
import os

# URL to your JSON
url = "https://raw.githubusercontent.com/apiusage/sg-4d-json/main/4d.json"

# Get the data
response = requests.get(url)
numbers = response.json()

# Extract first 3 numbers
first, second, third = numbers[:3]

# Get today's date in M/D/YYYY format
today = datetime.today().strftime('%-m/%-d/%Y')

# New row data
new_row = {
    "DrawDate": today,
    "1st": first,
    "2nd": second,
    "3rd": third
}

file_path = "4d_results.csv"

# Check if file exists and read or create
if os.path.exists(file_path):
    existing_df = pd.read_csv(file_path)
    
    # Only append if today's DrawDate is not already present
    if not (existing_df["DrawDate"] == today).any():
        updated_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        updated_df = existing_df
else:
    updated_df = pd.DataFrame([new_row])

# Save as CSV
updated_df.to_csv(file_path, index=False)
