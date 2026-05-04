import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from core.safe_get import safe_get

BASE = "https://weworkremotely.com"
MASTER_RSS = BASE + "/remote-jobs.rss"


def get_wwr_job_urls(keyword):
    urls = []

    response = safe_get(MASTER_RSS)
    if response == None:
        return urls

    root = ET.fromstring(response.content)
    items = root.findall(".//item")

    for item in items:
        title = item.findtext("title", "")
        desc = item.findtext("description", "")
        link = item.findtext("link", "")

        text = (title + " " + desc).lower()

        if keyword.lower() in text:
            if link != "":
                urls.append(link)

    return list(set(urls))


def get_wwr_job_details(job_url):
    response = safe_get(job_url)
    if response == None:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    job = {}

    job["job_url"] = job_url
    job["source"] = "WeWorkRemotely"

    title = soup.find("h1")
    job["job_title"] = title.get_text(strip=True) if title else None

    company = soup.select_one(".listing-header-container h2")
    job["company_name"] = company.get_text(strip=True) if company else None

    location = soup.select_one("span.region, span.location")
    job["location"] = location.get_text(strip=True) if location else "Remote"

   

    description_div = soup.find("div", {"id": "job-details"})
    
    if not description_div:
        description_div = soup.select_one(".listing-container")

    if description_div:
        for tag in description_div.find_all(["script", "style", "button", "div.apply-container"]):
            tag.decompose()

        text = description_div.get_text(separator="\n", strip=True)
        job["description"] = text[:5000] 
    else:
        job["description"] = "Description not found."

    return job