from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from scrapers import safe_get
from scrapers import save_prograss

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

LOCATION = "Egypt"






def get_job_ids(keyword, start):
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location={LOCATION}&start={start}"
    response = safe_get(url)
    if not response:
        return []

    job_soup = BeautifulSoup(response.text, "html.parser")
    page_jobs = job_soup.find_all('li')

    id_list = []
    for job in page_jobs:
        base_card_div = job.find("div", {"class": "base-card"})
        if base_card_div and base_card_div.get("data-entity-urn"):
            job_id = base_card_div.get("data-entity-urn").split(":")[3]
            id_list.append(job_id)
    return id_list


def get_job_details(job_id):
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    response = safe_get(url)

    if not response:
        return {"job_id": job_id, "job_url": f"https://www.linkedin.com/jobs/view/{job_id}/", "error": "failed"}

    job_soup = BeautifulSoup(response.text, "html.parser")
    job_post = {}

    job_post["job_url"] = f"https://www.linkedin.com/jobs/view/{job_id}/"

    try:
        job_post["job_title"] = job_soup.find("h2", {"class": "top-card-layout__title font-sans text-lg papabear:text-xl font-bold leading-open text-color-text mb-0 topcard__title"}).text.strip()
    except:
        job_post["job_title"] = None

    try:
        job_post["company_name"] = job_soup.find("a", {"class": "topcard__org-name-link topcard__flavor--black-link"}).text.strip()
    except:
        job_post["company_name"] = None

    try:
        job_post["time_posted"] = job_soup.find("span", {"class": "posted-time-ago__text topcard__flavor--metadata"}).text.strip()
    except:
        job_post["time_posted"] = None

    try:
        job_post["num_applicants"] = job_soup.find("span", {"class": "num-applicants__caption topcard__flavor--metadata topcard__flavor--bullet"}).text.strip()
    except:
        job_post["num_applicants"] = None

    try:
        job_post["location"] = job_soup.find("span", {"class": "topcard__flavor topcard__flavor--bullet"}).text.strip()
    except:
        job_post["location"] = None

    try:
        criteria = job_soup.find_all("li", {"class": "description__job-criteria-item"})
        for c in criteria:
            header = c.find("h3").text.strip().lower()
            value = c.find("span").text.strip()
            if "seniority" in header:
                job_post["seniority_level"] = value
            elif "employment" in header:
                job_post["employment_type"] = value
            elif "function" in header:
                job_post["job_function"] = value
            elif "industries" in header:
                job_post["industries"] = value
    except:
        job_post["seniority_level"] = None
        job_post["employment_type"] = None
        job_post["job_function"] = None
        job_post["industries"] = None

    try:
        desc_div = job_soup.find("div", {"class": "description__text description__text--rich"})
        if desc_div:
            for btn in desc_div.find_all("button"):
                btn.decompose()
            job_post["description"] = desc_div.get_text(separator="\n").strip()
        else:
            job_post["description"] = None
    except:
        job_post["description"] = None

    return job_post



all_jobs = []
seen_ids = set()

for keyword in KEYWORDS:
    print(f"scraping::'{keyword}'\n")
    keyword_ids = []
    start = 0

    while True:
        print(f"fetching ids from start :: {start}")
        ids = get_job_ids(keyword, start)

        if not ids:
            print(f"no more jobs for '{keyword}'")
            break

        #no dup ids
        new_ids = []
        for i in ids:
            if i not in seen_ids:
                new_ids.append(i)
        
        seen_ids.update(new_ids)
        keyword_ids.extend(new_ids)
        print(f"{len(new_ids)} new ids :::: unique postings :: {len(seen_ids)}")
        start += 10
        time.sleep(random.uniform(1, 3))


    # take the details from the ids
    for i, job_id in enumerate(keyword_ids):
        job_post = get_job_details(job_id)
        job_post["search_keyword"] = keyword
        all_jobs.append(job_post)

        # check point 
        save_prograss(all_jobs)
            
        time.sleep(random.uniform(1, 2))

    print(f"keyword :: '{keyword}' :: done with{len(keyword_ids)} jobs added")
    time.sleep(random.uniform(5, 10))


jobs_df = pd.DataFrame(all_jobs)
jobs_df.to_csv('listings.csv', index=False)