import json
from bs4 import BeautifulSoup
from core.safe_get import safe_get

BASE = "https://remoteok.com"

KEYWORD_TAGS = {
    "software engineer": ["software", "engineer", "javascript", "python"],
    "data scientist": ["data-science", "python", "machine-learning"],
    "data analyst": ["data", "analytics", "sql"],
    "machine learning engineer": ["machine-learning", "ai", "python"],
    "ai engineer": ["ai", "machine-learning", "python"],
    "backend developer": ["backend", "python", "node"],
    "frontend developer": ["frontend", "react", "javascript"],
    "full stack developer": ["fullstack", "react", "node"],
    "devops engineer": ["devops", "docker", "aws"],
    "cloud engineer": ["cloud", "aws"],
    "mobile developer": ["flutter", "ios", "android"],
    "python developer": ["python", "django"],
}


def get_remoteok_job_ids(keyword):
    ids = []
    seen = set()

    keyword = keyword.lower()

    if keyword in KEYWORD_TAGS:
        tags = KEYWORD_TAGS[keyword]
    else:
        tags = [keyword.split()[0]]

    for tag in tags:
        url = BASE + "/api?tag=" + tag
        response = safe_get(url)

        if response == None:
            continue

        try:
            data = response.json()
        except:
            continue

        for item in data:
            if type(item) == dict:
                if "id" in item:
                    job_id = str(item["id"])

                    if job_id not in seen:
                        seen.add(job_id)
                        ids.append(job_id)

    return ids


def get_remoteok_job_details(job_id):
    keyword_tags = []

    for values in KEYWORD_TAGS.values():
        for tag in values:
            if tag not in keyword_tags:
                keyword_tags.append(tag)

    entry = None

    for tag in keyword_tags:
        url = BASE + "/api?tag=" + tag
        response = safe_get(url)

        if response == None:
            continue

        try:
            data = response.json()
        except:
            continue

        for item in data:
            if type(item) == dict:
                if str(item.get("id")) == str(job_id):
                    entry = item
                    break

        if entry != None:
            break

    if entry == None:
        return None

    job = {}

    job["job_url"] = BASE + "/remote-jobs/" + str(job_id)
    job["source"] = "RemoteOK"

    job["job_title"] = entry.get("position")
    job["company_name"] = entry.get("company")

    if entry.get("location"):
        job["location"] = entry.get("location")
    else:
        job["location"] = "Remote"

    job["salary"] = entry.get("salary")
    job["date_posted"] = entry.get("date")

    tags = entry.get("tags")
    if tags:
        job["tags"] = ", ".join(tags)
    else:
        job["tags"] = None

    description = entry.get("description")

    if description:
        soup = BeautifulSoup(description, "html.parser")
        job["description"] = soup.get_text("\n", strip=True)[:3000]
    else:
        job["description"] = None

    return job