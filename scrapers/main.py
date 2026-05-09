"""
import time
import random
import pandas as pd

# New import from your core folder
from core.robots_checker import build_robot_parser, is_allowed

from core.safe_get import safe_get
from core.save_prograss import save_prograss

from remoteok import get_remoteok_job_ids, get_remoteok_job_details
from wuzz import get_wuzzuf_job_urls, get_wuzzuf_job_details

parsers = {
    "remoteok": build_robot_parser("https://remoteok.com"),
    "wuzzuf": build_robot_parser("https://wuzzuf.net")
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
    "python developer",
    "NLP engineer"
]

OUTPUT_FILE = "listings_combined.csv"

print("checking robots.txt for all targets")
remoteok_robots = build_robot_parser("https://remoteok.com")
wuzzuf_robots = build_robot_parser("https://wuzzuf.net")

all_jobs = []
seen_urls = set()

for keyword in KEYWORDS:
    print(f"--- Starting Keyword: {keyword} ---")
    targets = [] 

    if is_allowed(remoteok_robots, "https://remoteok.com/remote-jobs"):
        # Using IDs or paths as identifiers
        ids = get_remoteok_job_ids(keyword)
        for job_id in ids:
            if job_id not in seen_urls: # Using URL/Path as unique key
                seen_urls.add(job_id)
                targets.append((job_id, "remoteok"))

    # 4. Wuzzuf
    if is_allowed(wuzzuf_robots, "https://wuzzuf.net/search/jobs/"):
        for page in range(2):
            urls = get_wuzzuf_job_urls(keyword, page)
            for url in urls:
                if url not in seen_urls:
                    seen_urls.add(url)
                    targets.append((url, "wuzzuf"))

    print(f"Found {len(targets)} new job leads for '{keyword}'")

    # --- Detail Fetching Phase ---
    for identifier, site in targets:
        print(f"Fetching details from {site}: {identifier[-30:]}")
        
        job = None
        try:
            if site == "remoteok":
                job = get_remoteok_job_details(identifier)
            elif site == "wuzzuf":
                job = get_wuzzuf_job_details(identifier)

            if job:
                job["search_keyword"] = keyword
                job["site_source"] = site
                all_jobs.append(job)
                save_prograss(all_jobs)

        except Exception as e:
            print(f"Error scraping {identifier} on {site}: {e}")

        time.sleep(random.uniform(1.5, 3))

    print(f"Finished keyword: {keyword} | Total jobs collected: {len(all_jobs)}")
    time.sleep(random.uniform(5, 8))

save_prograss(all_jobs) 
df = pd.DataFrame(all_jobs)
df.to_csv(OUTPUT_FILE, index=False)

print(f"\nDONE! Total jobs saved: {len(df)} to {OUTPUT_FILE}")
"""