import requests
import pandas as pd
from datetime import datetime

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

file_path = "results.xlsx"

try:
    existing_df = pd.read_excel(file_path)

    # Only append if today’s DrawDate is not already present
    if not (existing_df["DrawDate"] == today).any():
        updated_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        updated_df = existing_df
except FileNotFoundError:
    # Create new file if not found
    updated_df = pd.DataFrame([new_row])

# Save the updated DataFrame
updated_df.to_excel(file_path, index=False)