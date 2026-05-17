
import requests
import json
import time
import random
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from core_wuzz.retry import with_retry
from core_wuzz.headers import get_headers_search
from core_wuzz.headers import get_headers_details
from core.loadExisting import load_existing_urls

"""
    format for refr::
    job_id, job_url, title, company_name, company_location, company_size,
    company_industry, status, job_type, years_of_exp, career_level, salary,
    description, requirements, created_at, updated_at, search_keyword
"""

SEARCH_API   = "https://wuzzuf.net/api/search/job"
DETAILS_API  = "https://wuzzuf.net/api/job"
PAGE_SIZE    = 100
OUTPUT_FILE  = "data/wuzzuf_listings.csv"
TEMP_JSON    = "data/wuzzuf_temp_new.json" 
MAX_PARALLEL = 3

KEYWORDS = [
    "software engineer", "data scientist", "data analyst",
    "machine learning engineer", "AI engineer",
    "backend developer", "frontend developer", "full stack developer",
    "DevOps engineer", "cloud engineer", "cybersecurity engineer",
    "mobile developer", "python developer", "NLP engineer",
    "computer vision engineer",
]

FINAL_COLS = [
    "job_id", "job_url", "title", "company_name", "company_location",
    "company_size", "company_industry", "status", "job_type",
    "years_of_exp", "career_level", "salary", "description",
    "requirements", "created_at", "updated_at", "search_keyword"
]




# wuzzuf expect on a json body not a get req 
def search_jobs(keyword: str, start_index: int = 0) -> list:
    def call():
        payload = json.dumps({
            "startIndex": start_index,
            "pageSize": PAGE_SIZE,
            "longitude": "0",
            "latitude": "0",
            "query": keyword,
            "searchFilters": {}
        })

        r = requests.post(
            SEARCH_API,
            headers=get_headers_search(),
            data=payload,
            timeout=15
        )

        jobs = []
        for job in r.json().get("data", []):
            jobs.append(job["id"])

        return (jobs, r.status_code)

    result = with_retry(call)

    if result is not None:
        return result
    else:
        return []

def get_job_details(job_ids: list) -> list:
    if not job_ids:
        return []
    def call():
        ids_str  = ",".join(job_ids) # id1,id2,id3
        url      = f"{DETAILS_API}?filter[other][ids]={ids_str}"
        req      = requests.Request("GET", url, headers=get_headers_details())
        prepared = req.prepare()
        prepared.url = url
        r = requests.Session().send(prepared, timeout=15)
        return (r.json().get("data", []), r.status_code)
    result = with_retry(call)
    
    if result is not None:
        return result
    else:
        return []
    

def parse_salary(salary_raw) -> str:
    
    if not salary_raw or not isinstance(salary_raw, dict):
        return None
    min_s = salary_raw.get("min")
    max_s = salary_raw.get("max")
    if min_s and max_s:
        return f"{min_s} - {max_s}"
    if max_s:
        return str(max_s)
    if min_s:
        return str(min_s)
    return None


def parse_job(job: dict, keyword: str) -> dict:
    attr = job.get("attributes", {})
    rels = job.get("relationships", {})

    company_id = None
    try:
        company_id = rels["company"]["data"]["id"]
    except (KeyError, TypeError):
        pass

    return {
        "job_id":       job.get("id"),
        "job_url":      f"https://wuzzuf.net/jobs/p/{job.get('id')}",
        "title":        attr.get("title"),
        "company_id":   company_id,          
        "company_name": None,                # company.py
        "company_location": None,            
        "company_size": None,                
        "company_industry": None,            
        "status":       attr.get("status"),
        "job_type":     attr.get("jobType"),
        "years_of_exp": attr.get("yearsOfExperience"),
        "career_level": attr.get("careerLevel"),
        "salary":       parse_salary(attr.get("salary")),
        "description":  attr.get("description"),
        "requirements": attr.get("requirements"),
        "created_at":   attr.get("createdAt"),
        "updated_at":   attr.get("updatedAt"),
        "search_keyword": keyword,
    }


def scrape_keyword(keyword: str, seen_ids: set, existing_urls: set,max_pages: int = 5) -> list:
    print(f"[wuzzuf] '{keyword}' starting:::")
    keyword_ids = []
    start = 0

    for page in range(max_pages):
        ids = search_jobs(keyword, start_index=start)
        if not ids:
            break
        new_ids = []
        for i in ids:
            if i not in seen_ids:
                new_ids.append(i)
        seen_ids.update(new_ids)
        keyword_ids.extend(new_ids)
        print(f"[wuzzuf] '{keyword}' page {page+1}: {len(new_ids)} new ids")
        if len(ids) < PAGE_SIZE:
            break
        start += PAGE_SIZE
        time.sleep(random.uniform(2, 4))

    filtered_ids = []

    for i in keyword_ids:
        url = f"https://wuzzuf.net/jobs/p/{i}"
        if url not in existing_urls:
            filtered_ids.append(i)
    
    keyword_ids = filtered_ids


    print(f"[wuzzuf] '{keyword}' {len(keyword_ids)} new IDs after dedup")

    jobs = []
    BATCH = 30
    for i in range(0, len(keyword_ids), BATCH):
        raw_jobs = get_job_details(keyword_ids[i:i + BATCH])
        for job in raw_jobs:
            jobs.append(parse_job(job, keyword))
        time.sleep(random.uniform(2, 5))

    print(f"[wuzzuf] '{keyword}' DONE with — {len(jobs)} jobs")
    return jobs


def scrape_all_parallel(keywords: list, max_pages: int = 5) -> list:
    seen_ids      = set()
    existing_urls = load_existing_urls(OUTPUT_FILE=OUTPUT_FILE , name="wuzzuf")
    all_jobs      = []

    print(f"\n[wuzzuf] {len(keywords)} keywords, {MAX_PARALLEL} at a time\n")

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as executor:
        futures = {
            executor.submit(scrape_keyword, kw, seen_ids, existing_urls, max_pages): kw
            for kw in keywords
        }
        for future in as_completed(futures):
            kw = futures[future]
            try:
                jobs = future.result()
                all_jobs.extend(jobs)
                for job in jobs:
                    if job.get("job_id"):
                        seen_ids.add(job["job_id"])
                print(f"\n[wuzzuf] '{kw}' done — total so far: {len(all_jobs)}\n")
            except Exception as e:
                print(f"\n[wuzzuf] ERROR in '{kw}': {e}\n")

    return all_jobs


def enrich_and_save(jobs: list):
    if not jobs:
        print("\n[wuzzuf] no new jobs to save")
        return

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(TEMP_JSON, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"\n[wuzzuf] Saved {len(jobs)} raw jobs to {TEMP_JSON}")

    print("[wuzzuf] Enriching with company data...")
    try:
        from company import fetch_companies

        company_ids = list({j["company_id"] for j in jobs if j.get("company_id")})
        company_map = {}
        BATCH = 50
        for i in range(0, len(company_ids), BATCH):
            batch  = company_ids[i:i + BATCH]
            result = fetch_companies(batch)
            company_map.update(result)
            print(f"  Fetched {len(company_map)}/{len(company_ids)} companies")
            time.sleep(random.uniform(1, 2))

        for job in jobs:
            cid  = job.get("company_id")
            info = company_map.get(cid, {})
            job["company_name"]     = info.get("company_name")
            job["company_location"] = info.get("company_location")
            job["company_size"]     = info.get("company_size")
            job["company_industry"] = info.get("company_industry")

    except Exception as e:
        print(f"  [wuzzuf] Company enrichment failed: {e} — saving without company details")

    df = pd.DataFrame(jobs)
    for col in FINAL_COLS:
        if col not in df.columns:
            df[col] = None
    df = df[FINAL_COLS]

    if os.path.exists(OUTPUT_FILE):
        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False)
        print(f"[wuzzuf] Appended {len(df)} enriched jobs to {OUTPUT_FILE}")
    else:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"[wuzzuf] Created {OUTPUT_FILE} with {len(df)} jobs")

    if os.path.exists(TEMP_JSON):
        os.remove(TEMP_JSON)


if __name__ == "__main__":
    jobs = scrape_all_parallel(KEYWORDS, max_pages=5)
    enrich_and_save(jobs)