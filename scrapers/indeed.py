

import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from jobspy import scrape_jobs
from core.loadExisting import load_existing_urls


OUTPUT_FILE  = "data/indeed_listings.csv"
MAX_PARALLEL = 3   

KEYWORDS = [
    "software engineer", "data scientist", "data analyst",
    "machine learning engineer", "AI engineer",
    "backend developer", "frontend developer", "full stack developer",
    "DevOps engineer", "cloud engineer", "cybersecurity engineer",
    "mobile developer", "python developer", "NLP engineer",
    "computer vision engineer",
]

STANDARD_COLS = [
    "job_id", "job_url", "search_keyword", "title", "company",
    "location", "salary", "job_type", "date", "description", "error"
]




def normalize(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    
    col_map = {
        "id":           "job_id",
        "job_url":      "job_url",        
        "title":        "title",          
        "company":      "company",        
        "location":     "location",       
        "date_posted":  "date",
        "job_type":     "job_type",       
        "description":  "description",   
    }

    out = pd.DataFrame()
    out["job_id"]        = df.get("id", pd.Series(dtype=str))
    out["job_url"]       = df.get("job_url", pd.Series(dtype=str))
    out["search_keyword"]= keyword
    out["title"]         = df.get("title", pd.Series(dtype=str))
    out["company"]       = df.get("company", pd.Series(dtype=str))
    out["location"]      = df.get("location", pd.Series(dtype=str))
    out["job_type"]      = df.get("job_type", pd.Series(dtype=str))
    out["date"]          = df.get("date_posted", pd.Series(dtype=str))
    out["description"]   = df.get("description", pd.Series(dtype=str))
    out["error"]         = None


    if "min_amount" in df.columns and "max_amount" in df.columns:
        salaries = []
        for _, row in df.iterrows():

            min_salary = row.get("min_amount")
            max_salary = row.get("max_amount")
            currency = row.get("currency", "")

            if pd.notna(min_salary) or pd.notna(max_salary):

                salary = f"{min_salary} - {max_salary} {currency}"
                salaries.append(salary.strip(" -"))

            else:
                salaries.append(None)
        out["salary"] = salaries

    else:
        out["salary"] = None


    return out[STANDARD_COLS]


def scrape_keyword(keyword: str, existing_urls: set) -> pd.DataFrame:
    print(f"[indeed] '{keyword}' starting:::")
    try:
        jobs = scrape_jobs(
            site_name=["indeed"],
            search_term=keyword,
            location="Egypt",
            country_indeed="Egypt",
            results_wanted=100,
            verbose=0,
        )

        if jobs is None or jobs.empty:
            print(f"[indeed] '{keyword}' :: got no results")
            return pd.DataFrame(columns=STANDARD_COLS)

        normalized = normalize(jobs, keyword)

        # dup
        new = normalized[~normalized["job_url"].isin(existing_urls)]
        existing_urls.update(new["job_url"].dropna().tolist())

        print(f"[indeed] '{keyword}' DONE with {len(new)} new jobs")
        return new

    except Exception as e:
        print(f"[indeed] ERROR in '{keyword}': {e}")
        return pd.DataFrame(columns=STANDARD_COLS)


def scrape_all_parallel(keywords: list) -> pd.DataFrame:
    existing_urls = load_existing_urls(OUTPUT_FILE=OUTPUT_FILE , name="indeed")
    results = []

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as executor:
        futures = {}
        for kw in keywords:
            future = executor.submit(scrape_keyword, kw, existing_urls)
            futures[future] = kw
        
        for future in as_completed(futures):
            kw = futures[future]
            try:
                df = future.result()
                if not df.empty:
                    results.append(df)
                print(f"[indeed] '{kw}' collected")
            except Exception as e:
                print(f"[indeed] ERROR '{kw}': {e}")
    if results:
        return pd.concat(results, ignore_index=True)
    else:
        return pd.DataFrame(columns=STANDARD_COLS)

def main():
    all_jobs = scrape_all_parallel(KEYWORDS)

    if all_jobs.empty:
        print("\n[indeed] problem with jobspy")
        return

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    if os.path.exists(OUTPUT_FILE):
        all_jobs.to_csv(OUTPUT_FILE, mode="a", header=False, index=False)
        print(f"\n[indeed] appended {len(all_jobs)} new jobs to {OUTPUT_FILE}")
    else:
        all_jobs.to_csv(OUTPUT_FILE, index=False)
        print(f"\n[indeed] created {OUTPUT_FILE} with {len(all_jobs)} jobs")


if __name__ == "__main__":
    main()