import sys
import os
import time
import subprocess
import shutil

ROOT          = os.path.dirname(os.path.abspath(__file__))
DATA_DIR      = os.path.join(ROOT, "data")
RETRIEVAL_DIR = os.path.join(ROOT, "retrieval")
SCRAPERS_DIR  = os.path.join(ROOT, "scrapers")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def stepLOG(title: str):
    print(f"\n{':::'*20}")
    print(f"{title}")
    print(f"{':::'*20}")

# dumb problem about versions
def _find_python() -> str:
    candidates = [sys.executable]

    for name in ["python", "python3", "python3.14", "python3.13", "python3.12", "python3.11"]:
        found = shutil.which(name)
        if found and found not in candidates:
            candidates.append(found)

    if sys.platform == "win32":
        import glob
        for pattern in [
            r"C:\Users\*\AppData\Local\Python\bin\python*.exe",
            r"C:\Users\*\AppData\Local\Programs\Python\Python3*\python.exe",
            r"C:\Python3*\python.exe",
        ]:
            for match in glob.glob(pattern):
                if match not in candidates:
                    candidates.append(match)

    for path in candidates:
        try:
            r = subprocess.run(
                [path, "-c", "import sentence_transformers, faiss"],
                capture_output=True, timeout=10
            )
            if r.returncode == 0:
                return path
        except Exception:
            continue

    print(f"WARNING: No Python with sentence_transformers+faiss found, using {sys.executable}")
    return sys.executable




def step_scrape():
    t = time.time()
    stepLOG("step1 ->>> (scraping)")

    if SCRAPERS_DIR not in sys.path:
        sys.path.insert(0, SCRAPERS_DIR)

    from scrapers import scrape
    scrape.main()
    return time.time() - t

def step_process():
    t = time.time()
    stepLOG("step2 ->>> ( Processing )")
    from processing import process
    ok = process.run(DATA_DIR)
    return ok, time.time() - t



def step_build_index():
    t = time.time()
    stepLOG("step3 ->>> ( Building search index )")

    build_index_path = os.path.join(RETRIEVAL_DIR, "build_index.py")
    
    # dump python binary problem
    python = _find_python()
    print(f"version ::: {python}")
    env = os.environ.copy()
    env["PYTHONPATH"] = RETRIEVAL_DIR + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run([python, build_index_path], cwd=ROOT, env=env)
    if result.returncode != 0:
        print("build_index.py FAILED")
        return False, 0
    return True, time.time() - t


def step_test_search():
    t = time.time()
    stepLOG("step4 ->>> ( search test ) ")
    _run_search("software engineer", top_k=10)
    return True, time.time() - t



def _run_search(query: str, top_k: int = 10):
    search_script = os.path.join(RETRIEVAL_DIR, "search.py")
    python= _find_python()

    env = os.environ.copy()
    env["PYTHONPATH"] = RETRIEVAL_DIR + os.pathsep + env.get("PYTHONPATH", "")

    subprocess.run(
        [python, search_script, query, str(top_k)],
        cwd=ROOT,
        env=env
    )


def main():
    args = sys.argv[1:]

    if args and not args[0].startswith("--"):
        query  = args[0]
        top_k  = int(args[1]) if len(args) > 1 else 10
        stepLOG(f"SEARCH: {query!r}")
        _run_search(query, top_k)
        return

    # pipeline mode 
    skip_scrape = "--skip-scrape" in args
    timings = {}
    start_all = time.time()

    if not skip_scrape:
        timings["scrape"] = step_scrape()
    else:
        stepLOG("scraping -> [SKIPPED]")

    ok, t = step_process()
    timings["process"] = t
    
    if not ok:
        print("\npipeline stopped (no data to process) [pipline]")
        return

    ok, t = step_build_index()
    timings["build_index"] = t
    if not ok:
        print("\npipeline stopped — (index build failed) [pipline]")
        return

    ok, t = step_test_search()
    timings["search_test"] = t

    
    total = time.time() - start_all
    
    stepLOG("pipeline DONE")
    print(f"{'Step':<15} {'Time':>8}")
    print(f"{'::'*10}")
    for step, elapsed in timings.items():
        mins, secs = divmod(int(elapsed), 60)
        print(f"  {step:<15} {mins}m {secs:02d}s")
    print(f"  {'-'*26}")
    mins, secs = divmod(int(total), 60)
    print(f"  {'TOTAL':<15} {mins}m {secs:02d}s")


if __name__ == "__main__":
    main()