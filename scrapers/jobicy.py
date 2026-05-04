import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from core.safe_get import safe_get

BASE = "https://jobicy.com"


def get_jobicy_job_urls(keyword):
    urls = []
    seen = set()

    response = safe_get(BASE + "/?feed=job_feed")

    if response != None:
        root = ET.fromstring(response.content)
        items = root.findall(".//item")

        for item in items:
            title = item.findtext("title", "")
            desc = item.findtext("description", "")
            link = item.findtext("link", "")

            text = title + desc

            if keyword.lower() in text.lower():
                if link not in seen:
                    seen.add(link)
                    urls.append(link)

    search = keyword.replace(" ", "+")

    for page in range(1, 6):

        if page == 1:
            url = BASE + "/?search_keywords=" + search
        else:
            url = BASE + "/page/" + str(page) + "/?search_keywords=" + search

        response = safe_get(url)

        if response == None:
            break

        soup = BeautifulSoup(response.text, "html.parser")
        found = False

        links = soup.find_all("a", href=True)

        for a in links:
            href = a["href"]

            if "/job/" in href:
                if href not in seen:
                    seen.add(href)
                    urls.append(href)
                    found = True

        if found == False:
            break

    return urls


def get_jobicy_job_details(job_url):
    response = safe_get(job_url)

    if response == None:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    job = {}

    job["job_url"] = job_url
    job["source"] = "Jobicy"

    title = soup.find("h1")
    if title != None:
        job["job_title"] = title.get_text(strip=True)
    else:
        job["job_title"] = None

    company = soup.select_one(".company-name, a[href*='/company/']")
    if company != None:
        job["company_name"] = company.get_text(strip=True)
    else:
        job["company_name"] = None

    location = soup.select_one(".location")
    if location != None:
        job["location"] = location.get_text(strip=True)
    else:
        job["location"] = "Remote"

    salary = soup.select_one(".salary")
    if salary != None:
        job["salary"] = salary.get_text(strip=True)
    else:
        job["salary"] = None

    description = soup.select_one(".job-description, .desc, .content")
    if description != None:
        job["description"] = description.get_text("\n", strip=True)[:3000]
    else:
        job["description"] = None

    return job