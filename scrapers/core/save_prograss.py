import pandas as pd
num = 50
name = "listings_prograssFile.csv"
def save_progress(all_jobs):
      if len(all_jobs) % num == 0:
        pd.DataFrame(all_jobs).to_csv(name, index=False)
        print(len(all_jobs))