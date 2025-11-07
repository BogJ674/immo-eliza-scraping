import subprocess
import pandas as pd
import time
import json
from pathlib import Path

# === CONFIG ===
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

SPIDERS = [
    "immovlan_apartments_by_municipality_1",
    "immovlan_apartments_by_municipality_2",
    "immovlan_apartments_by_municipality_3",
    "immovlan_houses_by_municipality_1",
    "immovlan_houses_by_municipality_2",
    "immovlan_houses_by_municipality_3",
]

APARTMENTS_COMBINED = DATA_DIR / "immo_apartments_combined.csv"
HOUSES_COMBINED = DATA_DIR / "immo_houses_combined.csv"
ALL_COMBINED = DATA_DIR / "immo_all_properties.csv"


# === 1. Run spiders sequentially with log files ===
def run_spider(spider_name):
    log_path = LOG_DIR / f"{spider_name}.log"
    print(f"\n🚀 Starting spider: {spider_name}")
    start = time.time()

    with open(log_path, "w", encoding="utf-8") as log_file:
        process = subprocess.run(
            ["scrapy", "crawl", spider_name],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=PROJECT_DIR,
            text=True,
        )

    elapsed = round(time.time() - start, 2)
    print(f"✅ Finished {spider_name} in {elapsed}s — log saved to {log_path}")
    return elapsed


total_start = time.time()
durations = {}

for spider in SPIDERS:
    durations[spider] = run_spider(spider)


# === 2. Combine CSVs ===
def combine_csvs(keyword, output_path):
    print(f"\n📦 Combining CSVs for '{keyword}' ...")
    csv_files = list(DATA_DIR.glob(f"*{keyword}*.csv"))
    if not csv_files:
        print(f"⚠️ No CSV files found for {keyword}")
        return None

    dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            df["source_file"] = f.name
            dfs.append(df)
        except Exception as e:
            print(f"⚠️ Failed to read {f}: {e}")

    if not dfs:
        print(f"⚠️ No valid CSVs for {keyword}")
        return None

    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.to_csv(output_path, index=False)
    print(f"✅ Saved → {output_path} ({len(combined_df)} rows)")
    return combined_df


apartments_df = combine_csvs("apartment", APARTMENTS_COMBINED)
houses_df = combine_csvs("house", HOUSES_COMBINED)

if apartments_df is not None and houses_df is not None:
    all_combined = pd.concat([apartments_df, houses_df], ignore_index=True)
    all_combined.to_csv(ALL_COMBINED, index=False)
    print(f"✅ Final merged CSV → {ALL_COMBINED}")
else:
    print("⚠️ Skipped full merge due to missing data.")


# === 3. Run cleaning script ===
print("\n🧹 Running clean_data.py ...")
clean_start = time.time()
subprocess.run(["python", "clean_data.py"], check=True)
clean_elapsed = round(time.time() - clean_start, 2)
print(f"✅ Data cleaning completed in {clean_elapsed}s.")


# === 4. Log runtime metrics ===
total_elapsed = round(time.time() - total_start, 2)
log_path = DATA_DIR / "run_all_metrics.json"
with open(log_path, "w", encoding="utf-8") as f:
    json.dump(
        {"total_runtime_s": total_elapsed, "durations": durations, "clean_time_s": clean_elapsed},
        f,
        indent=2,
    )
print(f"\n📊 Metrics saved → {log_path}")
