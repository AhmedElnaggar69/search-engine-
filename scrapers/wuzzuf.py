"""
Wuzzuf Job Scraper
Requirements: pip install requests
"""

import requests
import json
import time
import random

# ── Config ─────────────────────────────────────────────────────────────────────

SEARCH_API  = "https://wuzzuf.net/api/search/job"
DETAILS_API = "https://wuzzuf.net/api/job"
PAGE_SIZE   = 100

SEARCH_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept":       "application/json, text/plain, */*",
    "Referer":      "https://wuzzuf.net/",
    "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin":       "https://wuzzuf.net",
}

DETAILS_HEADERS = {
    # The details endpoint needs a different Accept — no strict JSON-only
    "Accept":       "application/vnd.api+json, application/json, */*",
    "Referer":      "https://wuzzuf.net/",
    "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin":       "https://wuzzuf.net",
}

KEYWORDS = [
    "software engineer",
    "data scientist",
    "data analyst",
    "machine learning engineer",
    "AI engineer",
    "backend developer",
    "frontend developer",
    "full stack developer",
    "DevOps engineer",
    "cloud engineer",
    "cybersecurity engineer",
    "mobile developer",
    "python developer",
    "NLP engineer",
    "computer vision engineer",
]


# ── Step 1: Search → get job IDs ───────────────────────────────────────────────

def search_jobs(keyword: str, start_index: int = 0) -> list[str]:
    payload = json.dumps({
        "startIndex":    start_index,
        "pageSize":      PAGE_SIZE,
        "longitude":     "0",
        "latitude":      "0",
        "query":         keyword,
        "searchFilters": {}
    })
    try:
        r = requests.post(SEARCH_API, headers=SEARCH_HEADERS,
                          data=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        return [job["id"] for job in data.get("data", [])]
    except Exception as e:
        print(f"  ❌ Search error: {e}")
        return []


# ── Step 2: Fetch job details — DON'T let requests encode the brackets ─────────

def get_job_details(job_ids: list[str]) -> list[dict]:
    if not job_ids:
        return []

    # Build URL manually so brackets stay unencoded (server requires this)
    ids_str = ",".join(job_ids)
    url = f"{DETAILS_API}?filter[other][ids]={ids_str}"

    try:
        # Use PreparedRequest to skip auto-encoding
        req = requests.Request("GET", url, headers=DETAILS_HEADERS)
        prepared = req.prepare()
        prepared.url = url          # override — keep raw brackets

        session = requests.Session()
        r = session.send(prepared, timeout=15)

        print(f"  Details status: {r.status_code}")

        if r.status_code != 200:
            print(f"  Response snippet: {r.text[:300]}")
            return []

        data = r.json()
        return data.get("data", [])

    except Exception as e:
        print(f"  ❌ Details error: {e}")
        return []


def parse_job(job: dict, keyword: str) -> dict:
    attr = job.get("attributes", {})
    rels = job.get("relationships", {})

    company_id = None
    try:
        company_id = rels["company"]["data"]["id"]
    except (KeyError, TypeError):
        pass

    return {
        "job_id":           job.get("id"),
        "job_url":          f"https://wuzzuf.net/jobs/p/{job.get('id')}",
        "title":            attr.get("title"),
        "status":           attr.get("status"),
        "job_type":         attr.get("jobType"),
        "years_of_exp":     attr.get("yearsOfExperience"),
        "career_level":     attr.get("careerLevel"),
        "salary":           attr.get("salary"),
        "description":      attr.get("description"),
        "requirements":     attr.get("requirements"),
        "created_at":       attr.get("createdAt"),
        "updated_at":       attr.get("updatedAt"),
        "company_id":       company_id,
        "search_keyword":   keyword,
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def scrape_all(keywords: list[str], max_pages_per_keyword: int = 5) -> list[dict]:
    all_jobs = []
    seen_ids = set()

    for keyword in keywords:
        print(f"\n🔍 Keyword: '{keyword}'")
        keyword_ids = []
        start = 0

        for page in range(max_pages_per_keyword):
            ids = search_jobs(keyword, start_index=start)
            if not ids:
                print(f"  No more results at page {page + 1}")
                break

            new_ids = [i for i in ids if i not in seen_ids]
            seen_ids.update(new_ids)
            keyword_ids.extend(new_ids)
            print(f"  Page {page + 1}: {len(new_ids)} new IDs (total unique: {len(seen_ids)})")

            if len(ids) < PAGE_SIZE:
                break

            start += PAGE_SIZE
            time.sleep(random.uniform(1, 2))

        # Fetch details in batches of 50
        BATCH = 50
        for i in range(0, len(keyword_ids), BATCH):
            batch = keyword_ids[i:i + BATCH]
            raw_jobs = get_job_details(batch)
            for job in raw_jobs:
                all_jobs.append(parse_job(job, keyword))
            print(f"  ✅ Parsed {len(raw_jobs)} job details")
            time.sleep(random.uniform(1, 2))

        time.sleep(random.uniform(3, 6))

    return all_jobs


if __name__ == "__main__":
    jobs = scrape_all(KEYWORDS, max_pages_per_keyword=5)
    print(f"\n🎯 Total jobs collected: {len(jobs)}")

    with open("wuzzuf_jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print("💾 Saved to wuzzuf_jobs.json")