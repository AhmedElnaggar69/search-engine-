import time 
import random
def with_retry(fn, retries=3, base_delay= 5.0):
    for attempt in range(retries):
        try:
            result, status = fn()
            if status in (429, 403):
                wait = base_delay * (2 ** attempt) + random.uniform(2, 5)
                print(f"[wuzzuf] rate limited ({status}) — waiting {wait:.0f}s")
                time.sleep(wait)
                continue
            return result
        except Exception as e:
            if attempt < retries - 1:
                wait = base_delay + random.uniform(1, 3)
                print(f"[wuzzuf] error: {e} — retrying in {wait:.0f}s")
                time.sleep(wait)
            else:
                print(f"[wuzzuf] failed after {retries} attempts: {e}")
    return None
