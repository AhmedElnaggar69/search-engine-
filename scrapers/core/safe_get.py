# safe get accouting for get blocked using some random timeouts  
import requests
import random
import time
from .headers import get_headers
from curl_cffi import requests

import cloudscraper

def safe_get_cap(url):
    # This creates a scraper instance that bypasses Cloudflare
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    try:
        response = scraper.get(url)
        return response
    except Exception as e:
        print(f"Connection error: {e}")
        return None
    
def safe_get(url, retries=5):
    for attempt in range(retries):
        try:
            #response = requests.get(url, headers=get_headers(), timeout=10)
            
            response = requests.get(
                url, 
                impersonate="chrome120", 
                headers={"User-Agent": "..."} # Use your rotation here
            )
            print(response.status_code)
            
            # If we get a 200, check if it's actually the content we want
            if response.status_code == 200:
                if "hcaptcha" in response.text or "cloudflare" in response.text:
                    print("Blocked by CAPTCHA/Cloudflare. Retrying...")
                    time.sleep(random.randint(5, 10))
                    continue
                return response

            if response.status_code == 429:
                wait = 60 + random.randint(10, 30)
                print(f"Rate limited. Sleeping for {wait}s")
                time.sleep(wait)
                continue

            # Handle other errors (403, 500, etc.)
            print(f"Received status code {response.status_code}. Attempt {attempt+1}")
            time.sleep(random.randint(5, 10))

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"Connection error: {e}. Retrying...")
            time.sleep(20)
    return None