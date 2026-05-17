
import sys
import time
import random
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed


def with_retry(fn, label: str, retries: int = 3, base_delay: float = 10.0):
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            err = str(e)
            if attempt < retries - 1:
                wait = base_delay * (2 ** attempt) + random.uniform(2, 5)
                print(f"  [{label}] error: {err[:100]}")
                print(f"  [{label}] retrying in {wait:.0f}s ({attempt+1}/{retries})")
                time.sleep(wait)
            else:
                print(f"  [{label}] failed after {retries} attempts: {err[:100]}")
                raise


def run_wuzzuf():
    from wuzzuf import scrape_all_parallel, enrich_and_save, KEYWORDS
    jobs = scrape_all_parallel(KEYWORDS, max_pages=5)
    enrich_and_save(jobs)


def run_linkedin():
    from Linkedin import main as linkedin_main
    with_retry(linkedin_main, label="linkedin")


def run_indeed():
    from indeed import main as indeed_main
    with_retry(indeed_main, label="indeed", retries=3, base_delay=15.0)


SCRAPERS = {
    "wuzzuf":   run_wuzzuf,
    "linkedin": run_linkedin,
    "indeed":   run_indeed,
}


def main():
    args = [a.lower() for a in sys.argv[1:]]
    targets = args if args else list(SCRAPERS.keys())

    unknown = [t for t in targets if t not in SCRAPERS]
    if unknown:
        print(f"Unknown: {', '.join(unknown)}. Valid: {', '.join(SCRAPERS)}")
        sys.exit(1)

    print(f"\nStarting: {', '.join(targets)}\n")
    start_all = time.time()
    results   = {}

    with ThreadPoolExecutor(max_workers=len(targets)) as executor:
        futures = {executor.submit(SCRAPERS[name]): name for name in targets}
        for future in as_completed(futures):
            name = futures[future]
            try:
                future.result()
                results[name] = "OK"
            except Exception as e:
                results[name] = f"FAILED: {e}"
                traceback.print_exc()
            print(f"[{name}] finished — {results[name]}")

    total = int(time.time() - start_all)
    print(f"\n{'='*40}")
    for name, status in results.items():
        print(f"  {name:<12} {status}")
    print(f"\n  Total: {total // 60}m {total % 60}s")
    print(f"{'='*40}")


if __name__ == "__main__":
    main()