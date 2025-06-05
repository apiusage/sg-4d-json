import requests
import pandas as pd
from datetime import datetime
import os

url = "https://raw.githubusercontent.com/apiusage/sg-4d-json/main/4d.json"

response = requests.get(url)
numbers = response.json()

first, second, third = numbers[:3]

today = datetime.now().strftime('%-m/%-d/%Y')

new_row = {
    "DrawDate": today,
    "1st": first,
    "2nd": second,
    "3rd": third
}

file_path = "4d_results.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    if not (df["DrawDate"] == today).any():
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
else:
    df = pd.DataFrame([new_row])

df.to_csv(file_path, index=False)
