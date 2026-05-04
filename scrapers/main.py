import time
import random
import pandas as pd

from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin

from core.safe_get import safe_get
from core.save_prograss import save_prograss

from wwr import get_wwr_job_urls, get_wwr_job_details
from jobicy import get_jobicy_job_urls, get_jobicy_job_details
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
    "NLP engineer"
]

OUTPUT_FILE = "listings_open2.csv"


def build_robot_parser(site_url):
    robots_url = urljoin(site_url, "/robots.txt")

    response = safe_get(robots_url)

    if response == None:
        return None

    if response.status_code != 200:
        return None

    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(response.text.splitlines())

    return parser


def is_allowed(parser, url):
    if parser == None:
        return True

    return parser.can_fetch("*", url)


print("checking robots.txt!!")

wwr_robots = build_robot_parser("https://weworkremotely.com")
jobicy_robots = build_robot_parser("https://jobicy.com")
remoteok_robots = build_robot_parser("https://remoteok.com")

print("ok")


all_jobs = []

seen_urls = set()
seen_ids = set()


for keyword in KEYWORDS:

    print("Scraping:", keyword)

    targets = []

    wwr_url = "https://weworkremotely.com/remote-jobs/search?term=" + keyword.replace(" ", "+")

    if is_allowed(wwr_robots, wwr_url):

        urls = get_wwr_job_urls(keyword)

        for url in urls:
            if url not in seen_urls:
                seen_urls.add(url)
                targets.append((url, "wwr"))


    jobicy_url = "https://jobicy.com/?feed=job_feed"

    if is_allowed(jobicy_robots, jobicy_url):

        urls = get_jobicy_job_urls(keyword)

        for url in urls:
            if url not in seen_urls:
                seen_urls.add(url)
                targets.append((url, "jobicy"))


    remoteok_url = "https://remoteok.com/api"

    if is_allowed(remoteok_robots, remoteok_url):

        ids = get_remoteok_job_ids(keyword)

        for job_id in ids:
            if job_id not in seen_ids:
                seen_ids.add(job_id)
                targets.append((job_id, "remoteok"))


    print("Found", len(targets), "new jobs")

    for target in targets:

        identifier = target[0]
        site = target[1]
        print(f"identifer {identifier} :: site {site}")

        if site == "wwr":
            job = get_wwr_job_details(identifier)

        elif site == "jobicy":
            job = get_jobicy_job_details(identifier)

        else:
            job = get_remoteok_job_details(identifier)

        if job != None:
            job["search_keyword"] = keyword
            all_jobs.append(job)

            save_prograss(all_jobs)

        time.sleep(random.uniform(1, 2))


    print("finshed with keyword:::", keyword)
    print("total jobs:", len(all_jobs))

    time.sleep(random.uniform(3, 5))


save_prograss(all_jobs, force=True)

df = pd.DataFrame(all_jobs)
df.to_csv(OUTPUT_FILE, index=False)

print("done::  saved ", len(df), "jobs to", OUTPUT_FILE)