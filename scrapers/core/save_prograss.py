import pandas as pd
import os

CHECKPOINT_FILE = "listings_progress.csv"
CHECKPOINT_EVERY = 10

def save_prograss(all_jobs, force=False):
    if not (force or (len(all_jobs) > 0 and len(all_jobs) % CHECKPOINT_EVERY == 0)):
        return
    try:
        pd.DataFrame(all_jobs).to_csv(CHECKPOINT_FILE, index=False)
        print(f"  [checkpoint] saved {len(all_jobs)} jobs")
    except PermissionError:
        # File is locked (open in Excel) — write to a temp file instead
        fallback = f"listings_progress_{len(all_jobs)}.csv"
        pd.DataFrame(all_jobs).to_csv(fallback, index=False)
        print(f"  [checkpoint] main file locked → saved to {fallback}")