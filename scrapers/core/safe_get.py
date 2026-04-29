# safe get accouting for get blocked using some random timeouts  
import requests
import random
import time
from scrapers import get_headers  
def safe_get(url, retries=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=get_headers(), timeout=10)

            if response.status_code == 429:
                wait = 60 + random.randint(10, 30)
                print(f"rate limit go to sleep : counting {wait}")
                time.sleep(wait)
                continue

            return response


        except requests.exceptions.ConnectionError as e:
            wait = 30 + random.randint(10, 20)
            print(f"con error attempt ::{attempt+1} out of :: {retries}  retries:: sleeping for {wait}:: error from request {e}")
            time.sleep(wait)

        except requests.exceptions.Timeout:
            wait = 15 + random.randint(5, 10)
            print(f"timeout attempt :: {attempt+1}out of :: {retries} retries:: Sleeping for {wait}")
            time.sleep(wait)
    return None 
