import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from core.safe_get import safe_get

BASE = "https://jobicy.com"

_FEED_CACHE: list[dict] | None = None   
MAX_HTML_PAGES = 5                       


def _fetch_rss_feed() -> list[dict]:
    global _FEED_CACHE
    if _FEED_CACHE is not None:
        return _FEED_CACHE

    _FEED_CACHE = []
    feed_url = f"{BASE}/?feed=job_feed"
    print(f"  [Jobicy] fetching RSS feed → {feed_url}")

    response = safe_get(feed_url)
    if not response:
        print("  [Jobicy] RSS feed unavailable")
        return _FEED_CACHE

    try:
        root    = ET.fromstring(response.content)
        channel = root.find("channel")
        items   = channel.findall("item") if channel else []

        for item in items:
            title_el = item.find("title")
            link_el  = item.find("link")
            desc_el  = item.find("description")

            title = (title_el.text or "").strip() if title_el is not None else ""
            url   = (link_el.text  or "").strip() if link_el  is not None else ""
            desc  = (desc_el.text  or "")         if desc_el  is not None else ""

            if url:
                _FEED_CACHE.append({"title": title, "url": url, "desc": desc})

    except ET.ParseError as e:
        print(f"Jobicy RSS parse error: {e}")

    return _FEED_CACHE


def _keyword_matches(text: str, kw_lower: str, kw_words: list[str]) -> bool:
    t = text.lower()
    return kw_lower in t or any(w in t for w in kw_words)


def get_jobicy_job_urls(keyword: str) -> list[str]:
 
    kw_lower = keyword.lower()
    kw_words = [w for w in kw_lower.split() if len(w) > 3]  #

    seen: set[str]  = set()
    urls: list[str] = []

    for entry in _fetch_rss_feed():
        text = entry["title"] + " " + entry["desc"]
        if _keyword_matches(text, kw_lower, kw_words):
            u = entry["url"]
            if u not in seen:
                seen.add(u)
                urls.append(u)

    search_kw = keyword.replace(" ", "+")
    for page in range(1, MAX_HTML_PAGES + 1):
        if page == 1:
            page_url = f"{BASE}/?search_keywords={search_kw}"
        else:
            page_url = f"{BASE}/page/{page}/?search_keywords={search_kw}"

        response = safe_get(page_url)
        if not response or response.status_code == 404:
            break

        soup = BeautifulSoup(response.text, "html.parser")
        found_on_page = 0

        for article in soup.find_all("article"):
            a = article.find("a", href=lambda h: h and "/job/" in h)
            if a and a["href"] not in seen:
                seen.add(a["href"])
                urls.append(a["href"])
                found_on_page += 1

        if found_on_page == 0:
            for a in soup.find_all("a", href=lambda h: h and "/job/" in h):
                if a["href"] not in seen:
                    seen.add(a["href"])
                    urls.append(a["href"])
                    found_on_page += 1

        if found_on_page == 0:
            break  

    print(f"  [Jobicy] {len(urls)} jobs matched '{keyword}'")
    return urls


# single page
def get_jobicy_job_details(job_url: str) -> dict:
    response = safe_get(job_url)
    if not response:
        return {"job_url": job_url, "source": "Jobicy", "error": "failed"}

    soup = BeautifulSoup(response.text, "html.parser")
    job  = {"job_url": job_url, "source": "Jobicy"}

    try:
        job["job_title"] = soup.find("h1").get_text(strip=True)
    except AttributeError:
        job["job_title"] = None

    try:
        tag = soup.select_one(".company-name, a[href*='/company/']")
        job["company_name"] = tag.get_text(strip=True) if tag else None
    except AttributeError:
        job["company_name"] = None

    try:
        loc = soup.select_one(".location")
        job["location"] = loc.get_text(strip=True) if loc else "Remote"
    except AttributeError:
        job["location"] = "Remote"

    try:
        sal = soup.select_one(".salary")
        job["salary"] = sal.get_text(strip=True) if sal else None
    except AttributeError:
        job["salary"] = None

    try:
        div = soup.select_one(".job-description, .desc, .content")
        if div:
            for tag in div.find_all(["button", "script", "style"]):
                tag.decompose()
            job["description"] = div.get_text(separator="\n").strip()[:3000]
        else:
            job["description"] = None
    except AttributeError:
        job["description"] = None

    return job