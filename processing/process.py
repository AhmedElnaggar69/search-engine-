import os
import re
import pandas as pd
from bs4 import BeautifulSoup


def clean_html(text):
    if not text or str(text).strip() in ("", "nan"):
        return ""
    text = str(text)
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def run(DATA_DIR: str) -> bool:
    
    
    WUZZUF_FILE   = os.path.join(DATA_DIR, "wuzzuf_listings.csv")
    INDEED_FILE   = os.path.join(DATA_DIR, "indeed_listings.csv")
    LINKEDIN_FILE = os.path.join(DATA_DIR, "linkedin_listings.csv")
    ALL_JOBS_FILE = os.path.join(DATA_DIR, "AllJobs.csv")
    WORKING_FILE  = os.path.join(DATA_DIR, "WorkingData.csv")

    frames = []

    if os.path.exists(WUZZUF_FILE):
        df1 = pd.read_csv(WUZZUF_FILE, dtype=str).fillna("")
        print(f"  Wuzzuf:   {len(df1):,} rows")
        frames.append(pd.DataFrame({
            "url":             df1.get("job_url", ""),
            "title":           df1.get("title", ""),
            "company":         df1.get("company_name", ""),
            "location":        df1.get("company_location", ""),
            "job_type":        df1.get("job_type", ""),
            "employment_type": df1.get("career_level", ""),
            "salary":          df1.get("salary", ""),
            "description":     df1.get("description", "").apply(clean_html),
            "requirements":    df1.get("requirements", "").apply(clean_html),
            "source":          "wuzzuf",
        }))
    else:
        print("someting went wrong with wuzzuf processing")

    if os.path.exists(INDEED_FILE):
        df2 = pd.read_csv(INDEED_FILE, dtype=str).fillna("")
        print(f"  Indeed:   {len(df2):,} rows")
        frames.append(pd.DataFrame({
            "url":             df2.get("job_url", ""),
            "title":           df2.get("title", ""),
            "company":         df2.get("company", ""),
            "location":        df2.get("location", ""),
            "job_type":        df2.get("job_type", ""),
            "employment_type": "",
            "salary":          df2.get("salary", ""),
            "description":     df2.get("description", "").apply(clean_html),
            "requirements":    "",
            "source":          "indeed",
        }))
    else:
        print("someting went wrong with indeed processing")

    # ── LinkedIn ───────────────────────────────────────────────────────────────
    if os.path.exists(LINKEDIN_FILE):
        df3 = pd.read_csv(LINKEDIN_FILE, dtype=str).fillna("")
        print(f"  LinkedIn: {len(df3):,} rows")
        is_old = "job_title" in df3.columns
        frames.append(pd.DataFrame({
            "url":             df3.get("job_url", ""),
            "title":           df3["job_title"]       if is_old else df3.get("title", ""),
            "company":         df3["company_name"]    if is_old else df3.get("company", ""),
            "location":        df3.get("location", ""),
            "job_type":        df3["seniority_level"] if is_old else df3.get("job_type", ""),
            "employment_type": df3["employment_type"] if is_old else "",
            "salary":          "",
            "description":     df3.get("description", "").apply(clean_html),
            "requirements":    "",
            "source":          "linkedin",
        }))
    else:
        print("someting went wrong with linkedin processing")

    if not frames:
        print("\n csv files not found")
        return False

    merged = pd.concat(frames, ignore_index=True)
    merged = merged[merged["url"].str.strip() != ""]
    merged.to_csv(ALL_JOBS_FILE, index=False, encoding="utf-8-sig")
    print(f"\n  AllJobs.csv:     {len(merged):,} rows → {ALL_JOBS_FILE}")

    before  = len(merged)
    working = merged.drop_duplicates(subset=["url"]).copy()
    working.to_csv(WORKING_FILE, index=False, encoding="utf-8-sig")
    print(f"  WorkingData.csv: {len(working):,} rows (removed {before - len(working):,} dupes) → {WORKING_FILE}")

    return True


if __name__ == "__main__":
    ROOT= os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(ROOT, "data")
    run(DATA_DIR)