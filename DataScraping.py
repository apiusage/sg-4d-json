import json, re, threading, requests, pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "https://www.singaporepools.com.sg/_layouts/15/FourD/FourDCommon.aspx/Get4DNumberCheckResultsJSON"
OUT = "4d_history_results.csv"
SGT = ZoneInfo("Asia/Singapore")
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.singaporepools.com.sg/en/product/Pages/4d_cpwn.aspx",
}
PRIZE = {"1": "1st", "2": "2nd", "3": "3rd", "S": "Starter", "C": "Consolation"}
thread_local = threading.local()

def session():
    if not hasattr(thread_local, "s"):
        thread_local.s = requests.Session()
        thread_local.s.headers.update(HEADERS)
    return thread_local.s

def parse_date(x):
    ts = int(re.search(r"\d+", x).group()) / 1000
    return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(SGT).strftime("%Y-%m-%d")

def fetch(n):
    try:
        r = session().post(URL, json={
            "numbers": [n],
            "checkCombinations": "false",
            "sortTypeInteger": "1"
        }, timeout=10)
        if r.status_code != 200:
            return None
        data = json.loads(r.json()["d"]).get("data", [])
        if not data:
            return None
        prizes = data[0].get("Prizes", [])
        if not prizes:
            return None
        rows = []
        for x in prizes:
            code = str(x["PrizeCode"])
            if code not in PRIZE:
                continue
            rows.append({
                "DrawDate": parse_date(x["DrawDate"]),
                "Prize": PRIZE[code],
                "Number": n
            })
        return rows
    except:
        return None

def scrape():
    queries = [str(i).zfill(4) for i in range(10000)]
    all_rows = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        fs = {ex.submit(fetch, q): q for q in queries}
        for i, f in enumerate(as_completed(fs), 1):
            r = f.result()
            if r:
                all_rows.extend(r)
            if i % 500 == 0:
                print(f"{i} / {len(queries)}")
    return all_rows

def build_csv(all_rows):
    df = pd.DataFrame(all_rows)
    if df.empty:
        print("ERROR: No data scraped.")
        return
    pivot = (
        df.groupby(["DrawDate", "Prize"])["Number"]
        .apply(lambda x: "|".join(sorted(x)))
        .unstack(fill_value="")
        .reset_index()
    )
    prize_order = ["1st", "2nd", "3rd", "Starter", "Consolation"]
    cols = ["DrawDate"] + [p for p in prize_order if p in pivot.columns]
    pivot = pivot[cols]
    pivot.insert(1, "Day", pd.to_datetime(pivot["DrawDate"]).dt.strftime("%a"))
    pivot.sort_values("DrawDate").to_csv(OUT, index=False)
    print("saved:", OUT)

def main():
    all_rows = scrape()
    build_csv(all_rows)

if __name__ == "__main__":
    main()