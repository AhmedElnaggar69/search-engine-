import os
import pandas as pd

def load_existing_urls(OUTPUT_FILE , name) -> set:
    if not os.path.exists(OUTPUT_FILE):
        print("first run for wuzzuf :: populating")
        return set()
    try:
        # get job_url to later use for dup
        df = pd.read_csv(OUTPUT_FILE, usecols=["job_url"], dtype=str)
        urls = set(df["job_url"].dropna().str.strip())
        print(f"[{name}] Loaded {len(urls):,} existing url")
        return urls
    except Exception as e:
        print(f"[wuzzuf] exception: {e}")
        return set()

