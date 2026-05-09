from seleniumbase import SB
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import json
import os
import sys

_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
COOKIES_FILE = os.path.join(_SCRIPT_DIR, "indeed_cookies.json")

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

LOC             = "Egypt"
OUTPUT_IDS      = os.path.join(_SCRIPT_DIR, "indeed_collected_ids.csv")
OUTPUT_PROGRESS = os.path.join(_SCRIPT_DIR, "indeed_progress.csv")
OUTPUT_FINAL    = os.path.join(_SCRIPT_DIR, "indeed_final_results.csv")

MAX_PAGES_CEILING   = 70
DELAY_BETWEEN_PAGES = (5, 10)
DELAY_BETWEEN_JOBS  = (3,  7)



def load_cookies(filepath: str) -> list[dict]:
    if not os.path.exists(filepath):
        print(f"ERROR: Cookie file not found: {filepath}")
        print("Export your cookies from eg.indeed.com using Cookie-Editor and save as indeed_cookies.json")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            cookies = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: {filepath} is not valid JSON: {e}")
            sys.exit(1)

    print(f"  Loaded {len(cookies)} cookies from {filepath}")
    return cookies


def inject_cookies(sb, cookies: list[dict]):
    injected = 0
    skipped  = 0

    for cookie in cookies:
        try:
            clean = {
                "name":   cookie.get("name",   ""),
                "value":  cookie.get("value",  ""),
                "path":   cookie.get("path",   "/"),
                "secure": cookie.get("secure", False),
            }

            domain = cookie.get("domain", ".indeed.com")
            if domain.startswith("."):
                domain = domain[1:]
            clean["domain"] = domain

            if "indeed.com" not in clean["domain"]:
                skipped += 1
                continue

            if "expirationDate" in cookie:
                clean["expiry"] = int(cookie["expirationDate"])

            sb.add_cookie(clean)
            injected += 1

        except Exception:
            skipped += 1

    print(f"  Injected {injected} cookies  ({skipped} skipped)")



def humanize(sb, scroll_times: int = 3):
    for _ in range(scroll_times):
        try:
            sb.execute_script(f"window.scrollBy(0, {random.randint(250, 650)});")
        except Exception:
            pass
        time.sleep(random.uniform(0.8, 1.8))


def get_total_pages(soup) -> int:
    import re
    total_jobs = None

    candidates = [
        soup.find("div", class_=lambda c: c and "jobCountAndSortPane" in (c or "")),
        soup.find("div", id="searchCountPages"),
        soup.find("div", class_=lambda c: c and "ResultsCount" in (c or "")),
    ]

    for el in candidates:
        if el:
            text = el.get_text(" ", strip=True).replace(",", "")
            numbers = re.findall(r"\d+", text)
            if numbers:
                total_jobs = max(int(n) for n in numbers)
                break

    if total_jobs is None:
        return MAX_PAGES_CEILING if MAX_PAGES_CEILING else 10

    pages = (total_jobs + 9) // 10
    if MAX_PAGES_CEILING:
        pages = min(pages, MAX_PAGES_CEILING)

    return max(pages, 1)



def collect_all_job_ids(sb) -> list[dict]:
    collected = []
    seen_ids  = set()

    print("\n" + "=" * 60)
    print("  PHASE 1 — Collecting job IDs")
    print("=" * 60)

    for keyword in KEYWORDS:
        print(f"\n  Keyword: '{keyword}'")

        formatted = keyword.replace(" ", "+")
        first_url = f"https://eg.indeed.com/jobs?q={formatted}&l={LOC}&start=0"

        print(f"  Loading page 1...")
        try:
            sb.uc_open_with_reconnect(first_url, reconnect_time=4)
        except Exception:
            sb.open(first_url)
        time.sleep(2)
        humanize(sb, scroll_times=3)

        first_soup  = BeautifulSoup(sb.get_page_source(), "html.parser")
        total_pages = get_total_pages(first_soup)
        print(f"  Total pages: {total_pages}")

        # process page 1
        job_cards = first_soup.find_all("a", attrs={"data-jk": True})
        new_ids   = []
        for card in job_cards:
            jk = card.get("data-jk")
            if jk and jk not in seen_ids:
                seen_ids.add(jk)
                collected.append({"keyword": keyword, "job_id": jk})
                new_ids.append(jk)
        print(f"  Page 1: {len(job_cards)} cards → {len(new_ids)} new  (total: {len(collected)})")

        if len(job_cards) == 0:
            print("  No cards found — skipping keyword")
            continue

        time.sleep(random.uniform(*DELAY_BETWEEN_PAGES))

        # pages 2 onwards
        consecutive_empty = 0
        EMPTY_PAGE_LIMIT  = 3

        for page_num in range(1, total_pages):
            start_offset = page_num * 10
            url = f"https://eg.indeed.com/jobs?q={formatted}&l={LOC}&start={start_offset}"

            print(f"  Page {page_num + 1}/{total_pages}")
            try:
                sb.uc_open_with_reconnect(url, reconnect_time=4)
            except Exception:
                sb.open(url)
            time.sleep(2)
            humanize(sb, scroll_times=3)

            soup      = BeautifulSoup(sb.get_page_source(), "html.parser")
            job_cards = soup.find_all("a", attrs={"data-jk": True})

            new_ids = []
            for card in job_cards:
                jk = card.get("data-jk")
                if jk and jk not in seen_ids:
                    seen_ids.add(jk)
                    collected.append({"keyword": keyword, "job_id": jk})
                    new_ids.append(jk)

            print(f"  {len(job_cards)} cards → {len(new_ids)} new  (total: {len(collected)})")

            if len(job_cards) == 0:
                print("  Empty page — stopping this keyword")
                break

            if len(new_ids) == 0:
                consecutive_empty += 1
                if consecutive_empty >= EMPTY_PAGE_LIMIT:
                    print(f"  {EMPTY_PAGE_LIMIT} pages with 0 new IDs — moving to next keyword")
                    break
            else:
                consecutive_empty = 0

            time.sleep(random.uniform(*DELAY_BETWEEN_PAGES))

    print(f"\n  Phase 1 complete — {len(collected)} unique job IDs")

    if collected:
        pd.DataFrame(collected).to_csv(OUTPUT_IDS, index=False)
        print(f"  Saved to {OUTPUT_IDS}")

    return collected



def fetch_job_details(sb, job_id: str, keyword: str) -> dict:
    url = f"https://eg.indeed.com/viewjob?jk={job_id}"

    try:
        sb.uc_open_with_reconnect(url, reconnect_time=4)
    except Exception:
        sb.open(url)

    time.sleep(random.uniform(1.5, 3))
    humanize(sb, scroll_times=2)

    try:
        soup = BeautifulSoup(sb.get_page_source(), "html.parser")
        job  = {"job_id": job_id, "job_url": url, "search_keyword": keyword}

        t              = soup.find("h1", class_="jobsearch-JobInfoHeader-title")
        job["title"]   = t.get_text(strip=True) if t else None

        c              = soup.find("div", attrs={"data-company-name": "true"})
        job["company"] = c.get_text(strip=True) if c else None

        sub = soup.find("div", class_="jobsearch-JobInfoHeader-subtitle")
        if sub:
            parts           = [d.get_text(" ", strip=True) for d in sub.find_all("div")]
            job["location"] = parts[-1] if parts else None
        else:
            job["location"] = None

        sal_div = soup.find("div", id="salaryInfoAndJobType")
        if sal_div:
            spans           = [s.get_text(strip=True) for s in sal_div.find_all("span") if s.get_text(strip=True)]
            job["salary"]   = next((t for t in spans if any(c in t for c in "$£€EGP")), None)
            job["job_type"] = next((t for t in spans if any(w in t.lower() for w in ["time", "contract", "temp"])), None)
        else:
            job["salary"]   = None
            job["job_type"] = None

        date_t       = soup.find("span", class_=lambda c: c and "date" in (c or "").lower())
        job["date"]  = date_t.get_text(strip=True) if date_t else None

        desc               = soup.find("div", id="jobDescriptionText")
        job["description"] = desc.get_text(separator="\n").strip() if desc else None

        return job

    except Exception as e:
        return {"job_id": job_id, "job_url": url, "search_keyword": keyword, "error": str(e)}


def collect_job_details(sb, id_records: list[dict]) -> list[dict]:
    # resume support
    done_ids = set()
    all_jobs = []

    if os.path.exists(OUTPUT_PROGRESS):
        try:
            existing = pd.read_csv(OUTPUT_PROGRESS)
            done_ids = set(existing["job_id"].dropna().astype(str).tolist())
            all_jobs = existing.to_dict("records")
            print(f"  Resuming — {len(done_ids)} jobs already done")
        except Exception:
            pass

    remaining = [r for r in id_records if r["job_id"] not in done_ids]

    print("\n" + "=" * 60)
    print(f"  PHASE 2 — Fetching details")
    print(f"  Total: {len(id_records)}  |  Done: {len(done_ids)}  |  Remaining: {len(remaining)}")
    print("=" * 60)

    if not remaining:
        print("  Nothing left to fetch.")
        return all_jobs

    for i, record in enumerate(remaining, start=1):
        job_id  = record["job_id"]
        keyword = record["keyword"]
        overall = len(done_ids) + i

        print(f"\n  [{overall}/{len(id_records)}]  {job_id}  ({keyword})")

        details = fetch_job_details(sb, job_id, keyword)
        all_jobs.append(details)

        print(f"  Title:   {str(details.get('title',   '?'))[:50]}")
        print(f"  Company: {str(details.get('company', '?'))[:40]}")

        # checkpoint every 20 jobs
        if i % 20 == 0:
            pd.DataFrame(all_jobs).to_csv(OUTPUT_PROGRESS, index=False)
            print(f"  Checkpoint saved ({overall}/{len(id_records)})")

        time.sleep(random.uniform(*DELAY_BETWEEN_JOBS))

    return all_jobs



def main():
    print("\n" + "=" * 60)
    print("  INDEED SCRAPER")
    print("=" * 60)

    cookies = load_cookies(COOKIES_FILE)

    with SB(uc=True, headless=False) as sb:
        sb.set_window_size(1400, 1000)

        print("\n  Opening Indeed homepage...")
        sb.open("https://eg.indeed.com")
        time.sleep(3)

        print("\n  Injecting cookies...")
        inject_cookies(sb, cookies)
        sb.refresh()
        time.sleep(3)

        # skip if already done
        if os.path.exists(OUTPUT_IDS):
            print(f"\n  Found existing ID file — loading saved IDs...")
            try:
                id_records = pd.read_csv(OUTPUT_IDS).to_dict("records")
                print(f"  Loaded {len(id_records)} job IDs")
            except Exception as e:
                print(f"  Could not read {OUTPUT_IDS}: {e} — running Phase 1")
                id_records = collect_all_job_ids(sb)
        else:
            id_records = collect_all_job_ids(sb)

        if not id_records:
            print("\n  No job IDs collected. Exiting.")
            return

        # Phase 2 — fetch details
        all_jobs = collect_job_details(sb, id_records)

    if all_jobs:
        pd.DataFrame(all_jobs).to_csv(OUTPUT_FINAL, index=False)

    print(f"\n  Done! {len(all_jobs)} jobs scraped.")
    print(f"  {OUTPUT_FINAL}")


if __name__ == "__main__":
    main()