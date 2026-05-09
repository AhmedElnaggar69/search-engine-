

import json
import time
import random
import requests
import pandas as pd

COMPANY_API = "https://wuzzuf.net/api/company"

HEADERS = {
    "Accept":     "application/vnd.api+json, application/json, */*",
    "Referer":    "https://wuzzuf.net/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin":     "https://wuzzuf.net",
}


def fetch_companies(company_ids: list[str]) -> dict[str, dict]:
    """Fetch company details for a batch of IDs. Returns {id: {name, location}}"""
    ids_str = ",".join(company_ids)
    url = f"{COMPANY_API}?filter[id]={ids_str}"

    try:
        req = requests.Request("GET", url, headers=HEADERS)
        prepared = req.prepare()
        prepared.url = url 

        session = requests.Session()
        r = session.send(prepared, timeout=15)

        if r.status_code != 200:
            print(f"api status{r.status_code}: {r.text[:200]}")
            return {}

        data = r.json().get("data", [])
        result = {}
        for company in data:
            cid  = company.get("id")
            attr = company.get("attributes", {})
            result[cid] = {
                "company_name":     attr.get("name"),
                "company_location": attr.get("city") or attr.get("location"),
                "company_size":     attr.get("size"),
                "company_industry": attr.get("industry"),
            }
        return result

    except Exception as e:
        pass
def enrich(input_file="wuzzuf_jobs.json", output_file="wuzzuf_jobs.csv"):
    with open(input_file, encoding="utf-8") as f:
        jobs = json.load(f)

    
    company_ids = list({j["company_id"] for j in jobs if j.get("company_id")})
    
    company_map = {}
    BATCH = 50
    for i in range(0, len(company_ids), BATCH):
        batch = company_ids[i:i + BATCH]
        result = fetch_companies(batch)
        company_map.update(result)
        print(f"  Fetched {len(company_map)}/{len(company_ids)} companies")
        time.sleep(random.uniform(1, 2))

    for job in jobs:
        cid = job.get("company_id")
        info = company_map.get(cid, {})
        job["company_name"]     = info.get("company_name")
        job["company_location"] = info.get("company_location")
        job["company_size"]     = info.get("company_size")
        job["company_industry"] = info.get("company_industry")

    df = pd.DataFrame(jobs)
    cols = ["job_id", "job_url", "title", "company_name", "company_location",
            "company_size", "company_industry", "status", "job_type",
            "years_of_exp", "career_level", "salary", "description",
            "requirements", "created_at", "updated_at", "search_keyword"]
    
    cols = [c for c in cols if c in df.columns]
    df = df[cols]

    df.to_csv(output_file, index=False)
    print(f"save {len(df)} jobs to {output_file}")


if __name__ == "__main__":
    enrich("wuzzuf_jobs.json", "wuzzuf_jobs.csv")