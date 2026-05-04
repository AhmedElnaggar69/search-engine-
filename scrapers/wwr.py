import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from core.safe_get import safe_get

BASE       = "https://weworkremotely.com"
MASTER_RSS = f"{BASE}/remote-jobs.rss"

_FEED_CACHE: list[dict] | None = None  


def _fetch_all_wwr_jobs() -> list[dict]:
    global _FEED_CACHE
    if _FEED_CACHE is not None:
        return _FEED_CACHE

    _FEED_CACHE = []
    print(f"  [WWR] fetching master RSS feed → {MASTER_RSS}")

    response = safe_get(MASTER_RSS)
    if not response:
        print("  [WWR] failed to fetch RSS feed")
        return _FEED_CACHE

    try:
        root    = ET.fromstring(response.content)
        channel = root.find("channel")
        items   = channel.findall("item") if channel else []

        for item in items:
            title_el = item.find("title")
            link_el  = item.find("link")
            desc_el  = item.find("description")

            raw_title = (title_el.text or "").strip() if title_el is not None else ""
            url       = (link_el.text  or "").strip() if link_el  is not None else ""
            desc_html = (desc_el.text  or "")         if desc_el  is not None else ""

            if not url:
                continue

            # WWR titles follow the format: "Company — Job Title"
            parts       = raw_title.split("\u2014", 1)
            company     = parts[0].strip() if len(parts) == 2 else ""
            title       = parts[1].strip() if len(parts) == 2 else raw_title

            desc_text = ""
            if desc_html:
                desc_text = (
                    BeautifulSoup(desc_html, "html.parser")
                    .get_text(separator="\n")
                    .strip()[:3000]
                )

            _FEED_CACHE.append({
                "job_title":    title,
                "company_name": company,
                "job_url":      url,
                "location":     "Remote",
                "description":  desc_text,
                "source":       "WeWorkRemotely",
            })

    except ET.ParseError as e:
        print(f"  [WWR] RSS parse error: {e}")

    print(f"  [WWR] feed cached — {len(_FEED_CACHE)} total jobs")
    return _FEED_CACHE


def get_wwr_job_urls(keyword: str) -> list[str]:
    """
    Filter cached RSS jobs by keyword.
    Matches on full phrase OR any meaningful word in the keyword.
    """
    all_jobs = _fetch_all_wwr_jobs()
    kw_lower = keyword.lower()
    kw_words = [w for w in kw_lower.split() if len(w) > 3]  # skip short words

    matched = []
    for job in all_jobs:
        text = (job["job_title"] + " " + job["description"]).lower()
        if kw_lower in text or any(w in text for w in kw_words):
            matched.append(job["job_url"])

    unique = list(dict.fromkeys(matched))  # preserve order while deduplicating
    print(f"  [WWR] {len(unique)} jobs matched '{keyword}'")
    return unique


def get_wwr_job_details(job_url: str) -> dict:
    """
    Return the cached RSS entry for this URL (already has all fields).
    Falls back to scraping the job page only if the URL isn't in the cache.
    """
    cached = next(
        (j for j in (_FEED_CACHE or []) if j["job_url"] == job_url), None
    )
    if cached:
        return cached

    # ── Fallback: scrape the individual job page ───────────────────────────
    response = safe_get(job_url)
    if not response:
        return {"job_url": job_url, "source": "WeWorkRemotely", "error": "failed"}

    soup = BeautifulSoup(response.text, "html.parser")
    job  = {"job_url": job_url, "source": "WeWorkRemotely"}

    # Job title — always in the page's <h1>
    try:
        job["job_title"] = soup.find("h1").get_text(strip=True)
    except AttributeError:
        job["job_title"] = None

    # Company name — sits inside .listing-header-container > h2
    try:
        tag = soup.select_one(".listing-header-container h2")
        job["company_name"] = tag.get_text(strip=True) if tag else None
    except AttributeError:
        job["company_name"] = None

    # Location — in span.region or span.location
    try:
        loc = soup.select_one("span.region, span.location")
        job["location"] = loc.get_text(strip=True) if loc else "Remote"
    except AttributeError:
        job["location"] = "Remote"

    # Description — in div.listing-container
    try:
        div = soup.select_one("div.listing-container")
        if div:
            for tag in div.find_all(["button", "script", "style"]):
                tag.decompose()
            job["description"] = div.get_text(separator="\n").strip()[:3000]
        else:
            job["description"] = None
    except AttributeError:
        job["description"] = None

    return job