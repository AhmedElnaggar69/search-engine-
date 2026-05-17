from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import concurrent.futures
import os 
from core.safe_get import safe_get
from core.save_prograss import save_prograss

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
FILE_PATH = "data/linkedin_listings.csv" 


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
    time.sleep(random.uniform(0.5, 2))
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


def main():
    all_jobs = []
    seen_ids = set()
    MAX_WORKERS = 5

    if os.path.exists(FILE_PATH):
        try:
            print(f"Lloading existing database from {FILE_PATH}...")
            existing_df = pd.read_csv(FILE_PATH)
            if 'job_url' in existing_df.columns:
                for url in existing_df['job_url'].dropna():
                    try:
                        job_id = str(url).split('/view/')[1].strip('/')
                        seen_ids.add(job_id)
                    except IndexError:
                        continue
            print(f"loaded {len(seen_ids)} previously scraped jobs")
        except Exception as e:
            print(e)
    else:
        print("starting fresh")
        
    for keyword in KEYWORDS:
        print(f"\nscraping::'{keyword}'")
        keyword_ids = []
        start = 0

        while True:
            ids = get_job_ids(keyword, start)

            if not ids:
                print(f"no more jobs for '{keyword}'")
                break

            new_ids = []
            for i in ids:
                if i not in seen_ids:
                    new_ids.append(i)
            
            seen_ids.update(new_ids)
            keyword_ids.extend(new_ids)
            
            print(f"Start {start} :: Found {len(ids)} total IDs -> {len(new_ids)} are new/unique.")
            
            start += 10
            time.sleep(random.uniform(1, 3))

        if not keyword_ids:
            print(f"No new jobs found for '{keyword}', skipping details fetch.")
            continue

        print(f"starting {MAX_WORKERS} workers to fetch details for {len(keyword_ids)} new jobs")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            
            future_to_job = {}
            for job_id in keyword_ids:
                future = executor.submit(get_job_details, job_id)
                future_to_job[future] = job_id
            
            for future in concurrent.futures.as_completed(future_to_job):
                job_id = future_to_job[future]
                try:
                    job_post = future.result()
                    if "error" not in job_post:
                        job_post["search_keyword"] = keyword
                        all_jobs.append(job_post)
            
                        save_prograss(all_jobs)
                except Exception as exc:
                    print(f"job ID {job_id} made an exception: {exc}")

        print(f"keyword :: '{keyword}' :: done.")
        time.sleep(random.uniform(5, 10))


    if all_jobs:
        print(f"saving {len(all_jobs)} new listings to {FILE_PATH}...")
        
        os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
        
        jobs_df = pd.DataFrame(all_jobs)
        
        if os.path.exists(FILE_PATH):
            jobs_df.to_csv(FILE_PATH, mode='a', header=False, index=False)
        else:
            jobs_df.to_csv(FILE_PATH, index=False)
            
        print("save completed")
    else:
        print("scraping finished no jobs left")


if __name__ == "__main__":
    main()