

import json
from bs4 import BeautifulSoup
from core.safe_get import safe_get

BASE = "https://remoteok.com"

# Maps search keywords to the RemoteOK tag slugs used in their API
KEYWORD_TAGS: dict[str, list[str]] = {
    "software engineer":          ["software", "engineer", "javascript", "python"],
    "data scientist":             ["data-science", "python", "machine-learning", "statistics"],
    "data analyst":               ["data", "analytics", "sql", "python"],
    "machine learning engineer":  ["machine-learning", "ai", "python", "deep-learning"],
    "ai engineer":                ["ai", "machine-learning", "llm", "python"],
    "backend developer":          ["backend", "python", "node", "ruby", "go", "java"],
    "frontend developer":         ["frontend", "react", "vue", "javascript", "typescript"],
    "full stack developer":       ["fullstack", "javascript", "react", "node", "python"],
    "devops engineer":            ["devops", "kubernetes", "docker", "aws", "cloud"],
    "cloud engineer":             ["aws", "cloud", "gcp", "azure", "devops"],
    "cybersecurity engineer":     ["security", "cybersecurity", "infosec"],
    "mobile developer":           ["react-native", "flutter", "ios", "android", "mobile"],
    "python developer":           ["python", "django", "fastapi", "flask"],
    "nlp engineer":               ["nlp", "machine-learning", "python", "ai"],
    "computer vision engineer":   ["computer-vision", "python", "deep-learning", "ai"],
}

# Cache: tag slug → list of job dicts from the API
_TAG_CACHE: dict[str, list[dict]] = {}


def _fetch_tag_feed(tag: str) -> list[dict]:
    """Fetch (and cache) all RemoteOK jobs for a specific tag slug."""
    if tag in _TAG_CACHE:
        return _TAG_CACHE[tag]

    url = f"{BASE}/api?tag={tag}"
    response = safe_get(url)
    if not response:
        _TAG_CACHE[tag] = []
        return []

    try:
        data = response.json()
        # The API returns a legal notice dict as the first element — skip it
        jobs = [item for item in data if isinstance(item, dict) and "id" in item]
        _TAG_CACHE[tag] = jobs
        return jobs
    except (json.JSONDecodeError, TypeError) as e:
        print(f"  [RemoteOK] JSON error for tag '{tag}': {e}")
        _TAG_CACHE[tag] = []
        return []


def get_remoteok_job_ids(keyword: str) -> list[str]:
    """
    Collect job IDs from all tag feeds mapped to this keyword.
    Deduplicates across tags. Returns a list of string IDs.
    """
    kw_lower = keyword.lower()
    tags     = KEYWORD_TAGS.get(kw_lower, [kw_lower.split()[0]])  # fallback: first word

    seen_ids: set[str] = set()
    matched: list[str] = []
    total_fetched = 0

    for tag in tags:
        jobs = _fetch_tag_feed(tag)
        total_fetched += len(jobs)
        for job in jobs:
            job_id = str(job.get("id", ""))
            if job_id and job_id not in seen_ids:
                seen_ids.add(job_id)
                matched.append(job_id)

    print(f"  [RemoteOK] tags {tags} → {total_fetched} fetched, "
          f"{len(matched)} unique for '{keyword}'")
    return matched


def get_remoteok_job_details(job_id: str) -> dict:
    """
    Return details for a job ID by looking it up in the cached tag feeds.
    No extra HTTP request needed — everything is already in the cache.
    """
    # Search all cached feeds for this ID
    entry = None
    for jobs in _TAG_CACHE.values():
        entry = next((j for j in jobs if str(j.get("id")) == str(job_id)), None)
        if entry:
            break

    job_url = f"{BASE}/remote-jobs/{job_id}"
    job     = {"job_url": job_url, "source": "RemoteOK"}

    if not entry:
        job["error"] = "not_in_cache"
        return job

    job["job_title"]       = entry.get("position")
    job["company_name"]    = entry.get("company")
    job["location"]        = entry.get("location") or "Remote"
    job["salary"]          = entry.get("salary")
    job["employment_type"] = None
    job["tags"]            = ", ".join(entry.get("tags") or [])
    job["date_posted"]     = entry.get("date")

    # Description comes back as HTML — strip the tags
    raw_desc = entry.get("description") or ""
    if raw_desc:
        job["description"] = (
            BeautifulSoup(raw_desc, "html.parser")
            .get_text(separator="\n")
            .strip()[:3000]
        )
    else:
        job["description"] = None

    return job