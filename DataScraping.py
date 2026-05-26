import requests
import json
import pandas as pd
from datetime import datetime, timezone
import zoneinfo
import time
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

url = "https://www.singaporepools.com.sg/_layouts/15/FourD/FourDCommon.aspx/Get4DNumberCheckResultsJSON"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.singaporepools.com.sg/en/product/Pages/4d_cpwn.aspx"
}

SGT = zoneinfo.ZoneInfo("Asia/Singapore")
thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        s = requests.Session()
        s.headers.update(headers)
        thread_local.session = s
    return thread_local.session


def parse_date(x):
    ts = int(x.replace("/Date(", "").replace(")/", ""))
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).astimezone(SGT).strftime("%Y-%m-%d")


def clean_number(x):
    if x is None:
        return None
    s = re.sub(r"[^\d]", "", str(x))
    if len(s) != 4:
        return None
    return s.zfill(4)


def fetch(num, retries=3):
    query = str(num).zfill(4)
    payload = {
        "numbers": [query],
        "checkCombinations": "true",
        "sortTypeInteger": "1"
    }

    session = get_session()

    for attempt in range(retries):
        try:
            r = session.post(url, json=payload, timeout=10)

            if r.status_code == 429:
                wait = 2 ** attempt
                print(f"  [{query}] Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            if r.status_code != 200:
                print(f"  [{query}] HTTP error: {r.status_code}")
                return None, "http_error"

            data = r.json()
            inner = json.loads(data["d"])

        except Exception as e:
            print(f"  [{query}] Attempt {attempt+1} failed: {e}")
            time.sleep(1)
            continue

        if not inner.get("data"):
            return None, "no_data"

        rows = []
        for record in inner["data"]:
            number = clean_number(record.get("Number"))
            if number != query:
                continue
            for p in record.get("Prizes", []):
                rows.append({
                    "DrawDate": parse_date(p.get("DrawDate")),
                    "PrizeCode": str(p.get("PrizeCode")),
                    "Number": number
                })

        if not rows:
            return None, "no_data"

        df = pd.DataFrame(rows)
        df = df[df["Number"].notna()]
        df["Number"] = df["Number"].astype(str)
        return df, "ok"

    return None, "failed"


# -------------------------
# TRACKING
# -------------------------
all_data = []
lock = threading.Lock()
completed = 0
total = 10000
failed_numbers = set()
no_data_numbers = set()

WORKERS = 10


def process(i):
    global completed
    df, status = fetch(i)
    query = str(i).zfill(4)

    with lock:
        completed += 1
        if completed % 500 == 0:
            print(f"Progress: {completed}/{total} | Failed: {len(failed_numbers)} | No data: {len(no_data_numbers)}")

        if status == "ok" and df is not None and not df.empty:
            all_data.append(df)
        elif status == "no_data":
            no_data_numbers.add(query)
        else:
            failed_numbers.add(query)

    return df, status


# -------------------------
# FIRST PASS
# -------------------------
print(f"Starting {total} requests with {WORKERS} workers...")

with ThreadPoolExecutor(max_workers=WORKERS) as executor:
    futures = {executor.submit(process, i): i for i in range(total)}
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            i = futures[future]
            print(f"  [{str(i).zfill(4)}] Unhandled error: {e}")
            with lock:
                failed_numbers.add(str(i).zfill(4))

print(f"\nFirst pass done. Failed: {len(failed_numbers)} | No data: {len(no_data_numbers)}")


# -------------------------
# RETRY PASS
# -------------------------
if failed_numbers:
    print(f"\nRetrying {len(failed_numbers)} failed numbers with 5 workers...")
    retry_failed = set()

    def retry_process(n):
        df, status = fetch(int(n), retries=5)
        with lock:
            if status == "ok" and df is not None and not df.empty:
                all_data.append(df)
                failed_numbers.discard(n)
            elif status == "no_data":
                failed_numbers.discard(n)
                no_data_numbers.add(n)
            else:
                retry_failed.add(n)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(retry_process, n): n for n in list(failed_numbers)}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"  Retry error: {e}")

    print(f"Retry done. Still failed: {len(retry_failed)}")
    failed_numbers.update(retry_failed)


# -------------------------
# MISS REPORT
# -------------------------
with open("missed.txt", "w") as f:
    f.write("=== FAILED (errored, not collected) ===\n")
    if failed_numbers:
        f.write("\n".join(sorted(failed_numbers)))
    else:
        f.write("none")
    f.write(f"\n\n=== NO DATA ({len(no_data_numbers)} numbers never won any prize) ===\n")
    f.write("\n".join(sorted(no_data_numbers)))

print(f"\nMiss report saved: missed.txt")
print(f"Numbers that errored: {len(failed_numbers)}")
print(f"Numbers that never won: {len(no_data_numbers)}")
print(f"Numbers with data: {len(all_data)}")


# -------------------------
# BUILD DATAFRAME
# -------------------------
if not all_data:
    raise ValueError("No data collected.")

df = pd.concat(all_data, ignore_index=True)
df = df.drop_duplicates(subset=["DrawDate", "PrizeCode", "Number"])


def map_prize(x):
    return {
        "1": "1st",
        "2": "2nd",
        "3": "3rd",
        "S": "Starter",
        "C": "Consolation"
    }.get(str(x), str(x))


df["Prize"] = df["PrizeCode"].apply(map_prize)

pivot = (
    df.groupby(["DrawDate", "Prize"])["Number"]
    .apply(lambda x: ",".join(sorted(set(x.astype(str)))))
    .unstack()
)

order = ["1st", "2nd", "3rd", "Starter", "Consolation"]
pivot = pivot.reindex(columns=order).fillna("").reset_index()

pivot["Day"] = pd.to_datetime(pivot["DrawDate"]).dt.strftime("%a")
pivot = pivot[["DrawDate", "Day"] + order]


# -------------------------
# SAVE AS XLSX (TEXT FORMAT)
# -------------------------
output = "4d_grouped.xlsx"

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    pivot.to_excel(writer, index=False, sheet_name="4D")
    ws = writer.sheets["4D"]

    prize_col_indices = [pivot.columns.get_loc(c) + 1 for c in order]

    for col_idx in prize_col_indices:
        for row_idx in range(2, ws.max_row + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.number_format = "@"

print(f"\nSaved: {output}")