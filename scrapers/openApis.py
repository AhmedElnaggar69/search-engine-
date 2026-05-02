
import csv
import json
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

CONFIG = {
    "remoteok":   {"enabled": True,  "max_jobs": 500},
    "hackernews": {"enabled": True,  "max_jobs": 500},
    "himalayas":  {"enabled": True,  "max_jobs": 500},
    "arbeitnow":  {"enabled": True,  "max_jobs": 500},
    "jobicy":     {"enabled": True,  "max_jobs": 100},   
    "delay":      1.0,  
    "output_csv":  "jobs.csv",
    "output_json": "jobs.json",
}


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobResearchBot/1.0; academic use)"
}


def strip_html(text: str) -> str:
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()


def get(url: str, params: dict = None) -> dict | list | None:
    """GET with basic error handling."""
    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=15)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"    [WARN] Request failed: {e}")
        return None


def fetch_remoteok(max_jobs: int = 500) -> list[dict]:
    print("  [RemoteOK] Fetching...")
    data = get("https://remoteok.com/remote-jobs.json")
    if not data:
        return []

    jobs_raw = data[1:]  
    jobs = []
    for job in jobs_raw[:max_jobs]:
        jobs.append({
            "id":          f"remoteok_{job.get('id', '')}",
            "source":      "remoteok",
            "source_url":  "https://remoteok.com",
            "title":       job.get("position", "").strip(),
            "company":     job.get("company", "").strip(),
            "location":    job.get("location", "").strip() or "Remote",
            "salary_min":  job.get("salary_min") or "",
            "salary_max":  job.get("salary_max") or "",
            "tags":        ", ".join(job.get("tags", []) or []),
            "date_posted": str(job.get("date", ""))[:10],
            "description": strip_html(job.get("description", "")),
            "url":         job.get("url", ""),
        })

    print(f"  [RemoteOK] Got {len(jobs)} jobs")
    return jobs


def fetch_hackernews(max_jobs: int = 500) -> list[dict]:
    print("  [HackerNews] Fetching latest 'Who is hiring?' thread...")

    search = get(
        "https://hn.algolia.com/api/v1/search",
        params={"query": "Ask HN: Who is hiring", "tags": "story", "hitsPerPage": 1}
    )
    if not search or not search.get("hits"):
        return []

    thread_id = search["hits"][0]["objectID"]
    thread_title = search["hits"][0].get("title", "")
    print(f"  [HackerNews] Thread: {thread_title}")

    jobs = []
    page = 0

    while len(jobs) < max_jobs:
        data = get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "tags":        f"comment,story_{thread_id}",
                "hitsPerPage": 200,
                "page":        page,
            }
        )
        if not data or not data.get("hits"):
            break

        hits = data["hits"]
        if not hits:
            break

        for comment in hits:
            text = comment.get("comment_text", "")
            if len(text) < 150:
                continue

            first_line = text.split("\n")[0]
            parts = [p.strip() for p in first_line.split("|")]

            company  = parts[0] if len(parts) > 0 else "Unknown"
            title    = parts[1] if len(parts) > 1 else "Software Engineer"
            location = parts[2] if len(parts) > 2 else "Remote"

            jobs.append({
                "id":          f"hn_{comment.get('objectID', '')}",
                "source":      "hackernews",
                "source_url":  "https://news.ycombinator.com",
                "title":       title.strip(),
                "company":     company.strip(),
                "location":    location.strip(),
                "salary_min":  "",
                "salary_max":  "",
                "tags":        "",
                "date_posted": str(comment.get("created_at", ""))[:10],
                "description": strip_html(text),
                "url":         f"https://news.ycombinator.com/item?id={comment.get('objectID', '')}",
            })

        total_pages = data.get("nbPages", 1)
        page += 1
        if page >= total_pages:
            break

        time.sleep(CONFIG["delay"])

    jobs = jobs[:max_jobs]
    print(f"  [HackerNews] Got {len(jobs)} job posts")
    return jobs


def fetch_himalayas(max_jobs: int = 500) -> list[dict]:
    print("  [Himalayas] Fetching (20/page)...")
    jobs = []
    offset = 0
    limit  = 20

    while len(jobs) < max_jobs:
        data = get(
            "https://himalayas.app/jobs/api",
            params={"limit": limit, "offset": offset}
        )
        if not data:
            break

        items = data.get("jobs", [])
        if not items:
            print("  [Himalayas] No more results.")
            break

        for job in items:
            loc = job.get("locationRestrictions")
            if isinstance(loc, list):
                loc = ", ".join(loc)
            jobs.append({
                "id":          f"himalayas_{job.get('slug', offset)}",
                "source":      "himalayas",
                "source_url":  "https://himalayas.app",
                "title":       job.get("title", "").strip(),
                "company":     job.get("companyName", "").strip(),
                "location":    loc or "Remote",
                "salary_min":  job.get("salaryMin", "") or "",
                "salary_max":  job.get("salaryMax", "") or "",
                "tags":        ", ".join(job.get("categories", []) or []),
                "date_posted": str(job.get("createdAt", ""))[:10],
                "description": strip_html(job.get("description", "")),
                "url":         f"https://himalayas.app/jobs/{job.get('slug', '')}",
            })

        print(f"  [Himalayas] offset={offset} → {len(items)} jobs (total: {len(jobs)})")

        total = data.get("total", 0)
        offset += limit
        if offset >= total or len(jobs) >= max_jobs:
            break

        time.sleep(CONFIG["delay"])

    jobs = jobs[:max_jobs]
    print(f"  [Himalayas] Done — {len(jobs)} jobs")
    return jobs



def fetch_arbeitnow(max_jobs: int = 500) -> list[dict]:
    print("  [Arbeitnow] Fetching (100/page)...")
    jobs = []
    page = 1

    while len(jobs) < max_jobs:
        data = get(
            "https://www.arbeitnow.com/api/job-board-api",
            params={"page": page}
        )
        if not data:
            break

        items = data.get("data", [])
        if not items:
            print("  [Arbeitnow] No more results.")
            break

        for job in items:
            ts = job.get("created_at")
            date_posted = (
                datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""
            )
            jobs.append({
                "id":          f"arbeitnow_{job.get('slug', page)}",
                "source":      "arbeitnow",
                "source_url":  "https://www.arbeitnow.com",
                "title":       job.get("title", "").strip(),
                "company":     job.get("company_name", "").strip(),
                "location":    job.get("location", "").strip() or "Remote",
                "salary_min":  "",
                "salary_max":  "",
                "tags":        ", ".join(job.get("tags", []) or []),
                "date_posted": date_posted,
                "description": strip_html(job.get("description", "")),
                "url":         job.get("url", ""),
            })

        print(f"  [Arbeitnow] page={page} → {len(items)} jobs (total: {len(jobs)})")

        links = data.get("links", {})
        if not links.get("next"):
            break

        page += 1
        time.sleep(CONFIG["delay"])

    jobs = jobs[:max_jobs]
    print(f"  [Arbeitnow] Done — {len(jobs)} jobs")
    return jobs



def fetch_jobicy(max_jobs: int = 100) -> list[dict]:
    count = min(max_jobs, 100)
    print(f"  [Jobicy] Fetching up to {count} jobs...")

    data = get(
        "https://jobicy.com/api/v2/remote-jobs",
        params={"count": count}
    )
    if not data:
        return []

    items = data.get("jobs", [])
    jobs = []
    for job in items:
        industry = job.get("jobIndustry", [])
        if isinstance(industry, list):
            industry = ", ".join(industry)
        jobs.append({
            "id":          f"jobicy_{job.get('id', '')}",
            "source":      "jobicy",
            "source_url":  "https://jobicy.com",
            "title":       job.get("jobTitle", "").strip(),
            "company":     job.get("companyName", "").strip(),
            "location":    job.get("jobGeo", "Remote").strip(),
            "salary_min":  job.get("annualSalaryMin", "") or "",
            "salary_max":  job.get("annualSalaryMax", "") or "",
            "tags":        industry,
            "date_posted": str(job.get("pubDate", ""))[:10],
            "description": strip_html(job.get("jobDescription", "")),
            "url":         job.get("url", ""),
        })

    print(f"  [Jobicy] Got {len(jobs)} jobs")
    return jobs



def deduplicate(jobs: list[dict]) -> list[dict]:
    """Remove duplicates by (title, company) pair (case-insensitive)."""
    seen = set()
    unique = []
    for job in jobs:
        key = (job["title"].lower().strip(), job["company"].lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique



COLUMNS = [
    "id", "source", "source_url", "title", "company",
    "location", "salary_min", "salary_max", "tags",
    "date_posted", "url", "description",
]


def export_csv(jobs: list[dict], path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(jobs)
    print(f"Saved CSV  → {path}")


def export_json(jobs: list[dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON → {path}")



def main():
    all_jobs = []

    sources = {
        "remoteok":   (fetch_remoteok,   CONFIG["remoteok"]["max_jobs"]),
        "hackernews": (fetch_hackernews, CONFIG["hackernews"]["max_jobs"]),
        "himalayas":  (fetch_himalayas,  CONFIG["himalayas"]["max_jobs"]),
        "arbeitnow":  (fetch_arbeitnow,  CONFIG["arbeitnow"]["max_jobs"]),
        "jobicy":     (fetch_jobicy,     CONFIG["jobicy"]["max_jobs"]),
    }

    for name, (fn, max_jobs) in sources.items():
        if not CONFIG[name]["enabled"]:
            print(f"[{name}] Skipped (disabled in CONFIG)")
            continue
        print(f"\n{'─'*50}")
        jobs = fn(max_jobs)
        all_jobs.extend(jobs)

    print(f"\n{'─'*50}")
    print(f"Total before deduplication : {len(all_jobs)}")
    all_jobs = deduplicate(all_jobs)
    print(f"Total after  deduplication : {len(all_jobs)}")

    print()
    export_csv(all_jobs,  CONFIG["output_csv"])
    export_json(all_jobs, CONFIG["output_json"])

    df = pd.DataFrame(all_jobs)
    print("\nJobs per source:")
    print(df["source"].value_counts().to_string())


if __name__ == "__main__":
    main()