
import time
import random
import pandas as pd
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin
from core.safe_get import safe_get

from core.save_prograss import save_prograss
from wwr     import get_wwr_job_urls,      get_wwr_job_details
from jobicy  import get_jobicy_job_urls,   get_jobicy_job_details
from remoteok import get_remoteok_job_ids, get_remoteok_job_details


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
    "NLP engineer",
]

OUTPUT_FILE = "listings.csv"

def build_robot_parser(site_url: str) -> RobotFileParser | None:
    robots_url = urljoin(site_url, "/robots.txt")
    response = safe_get(robots_url)          # use YOUR safe_get, not urllib
    if not response or response.status_code != 200:
        print(f"[robots.txt] could not fetch {robots_url} — defaulting to ALLOW")
        return None

    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(response.text.splitlines())  
    return parser



def is_allowed(parser: RobotFileParser | None, url: str) -> bool:
    if parser is None:
        return True                           # fetch failed → allow by default
    allowed = parser.can_fetch("*", url)
    if not allowed:
        print(f"  [robots.txt] disallowed: {url}")
    return allowed
# ─────────────────────────────────────────────────────────────
#  ROBOTS.TXT PARSERS  (initialised once before the main loop)
# ─────────────────────────────────────────────────────────────

print("Checking robots.txt for all sites…")
wwr_robots      = build_robot_parser("https://weworkremotely.com")
jobicy_robots   = build_robot_parser("https://jobicy.com")
remoteok_robots = build_robot_parser("https://remoteok.com")
print("robots.txt checks done.\n")

# ─────────────────────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────────────────────

all_jobs   = []
seen_urls  = set()   # for WWR & Jobicy  (URL-based)
seen_ids   = set()   # for RemoteOK      (ID-based)

for keyword in KEYWORDS:
    print(f"\n{'='*60}")
    print(f"scraping :: '{keyword}'")
    print(f"{'='*60}")

    keyword_targets: list[tuple[str, str]] = []  # (identifier, site_tag)

    # ── We Work Remotely ──────────────────────────────────────
    wwr_search_url = f"https://weworkremotely.com/remote-jobs/search?term={keyword.replace(' ', '+')}"
    if is_allowed(wwr_robots, wwr_search_url):
        urls = get_wwr_job_urls(keyword)
        new_wwr = [(u, "wwr") for u in urls if u not in seen_urls]
        seen_urls.update(u for u, _ in new_wwr)
        keyword_targets.extend(new_wwr)
    else:
        print("  [WWR] blocked by robots.txt — skipping")

    # ── Jobicy ────────────────────────────────────────────────
    jobicy_feed_url = "https://jobicy.com/?feed=job_feed"
    if is_allowed(jobicy_robots, jobicy_feed_url):
        urls = get_jobicy_job_urls(keyword)
        new_jobicy = [(u, "jobicy") for u in urls if u not in seen_urls]
        seen_urls.update(u for u, _ in new_jobicy)
        keyword_targets.extend(new_jobicy)
    else:
        print("  [Jobicy] blocked by robots.txt — skipping")

    remoteok_api_url = "https://remoteok.com/api"
    if is_allowed(remoteok_robots, remoteok_api_url):
        ids = get_remoteok_job_ids(keyword)
        new_ro = [(i, "remoteok") for i in ids if i not in seen_ids]
        seen_ids.update(i for i, _ in new_ro)
        keyword_targets.extend(new_ro)
    else:
        print("  [RemoteOK] blocked by robots.txt — skipping")

    print(f"\n  → {len(keyword_targets)} new unique jobs to fetch for '{keyword}'")

    for i, (identifier, site) in enumerate(keyword_targets):

        if site == "wwr":
            job_post = get_wwr_job_details(identifier)
        elif site == "jobicy":
            job_post = get_jobicy_job_details(identifier)
        else:  # remoteok
            job_post = get_remoteok_job_details(identifier)

        job_post["search_keyword"] = keyword
        all_jobs.append(job_post)

        # Checkpoint (every 10 jobs)
        save_prograss(all_jobs)

        time.sleep(random.uniform(1, 2.5))

    print(f"  keyword '{keyword}' done — {len(keyword_targets)} jobs added "
          f"| running total: {len(all_jobs)}")

    time.sleep(random.uniform(4, 8))  

save_prograss(all_jobs, force=True)   

jobs_df = pd.DataFrame(all_jobs)
jobs_df.to_csv(OUTPUT_FILE, index=False)
print(f"\nScraping complete — {len(jobs_df)} jobs saved to {OUTPUT_FILE}")