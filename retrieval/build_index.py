from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
import pickle
from preprocess import preprocess
df = pd.read_csv("data/WorkingData.csv")

#print(df.head())

# we need to combine columns into one string 
df["title_doc"] = (df["title"].fillna("").astype(str) + " " +
                    df["company"].fillna("").astype(str) + " " )

df["full_search_doc"] = (
    df["title"].fillna("").astype(str) + " " + df["title"].fillna("").astype(str) + " " + df["title"].fillna("").astype(str) + " "+
    df["company"].fillna("").astype(str) + " " +
    df["job_type"].fillna("").astype(str) + " " +
    df["employment_type"].fillna("").astype(str) + " " +
    df["requirements"].fillna("").astype(str) + " " +
    df["description"].fillna("").astype(str)
)
#print(df.loc[3, "full_search_doc"])
#print(df.loc[3, "title_doc"])


df["title_doc"] = df["title_doc"].apply(preprocess)
# raw for embedding
df["full_search_doc_raw"] = df["full_search_doc"]
df["full_search_doc"] = df["full_search_doc"].apply(preprocess)

#print(df.loc[3, "full_search_doc"])
#print(df.loc[3, "title_doc"])

# bm25 part


bm25_title = BM25Okapi(df["title_doc"].tolist())
bm25_full  = BM25Okapi(df["full_search_doc"].tolist())

# usage example 
"""
query = "software engineer python"
quiTokens = preprocess(query)

title_scores = bm25_title.get_scores(quiTokens)

full_scores = bm25_full.get_scores(quiTokens)
"""
df.to_pickle("data/jobs.pkl")
with open("bm25_title.pkl" , "wb") as f:
    pickle.dump(bm25_title ,f)

with open("bm25_full.pkl" , "wb") as f:
    pickle.dump(bm25_full ,f)

# embedding
model = SentenceTransformer('all-MiniLM-L6-v2')
print("started embedding wait for a while <><><> >>> ")
raw_docs = df["full_search_doc_raw"].tolist()
vectors = model.encode(raw_docs , show_progress_bar=True)

np.save("job_vectors.npy", vectors)

dims = vectors.shape[1]
index = faiss.IndexFlatL2(dims)
index.add(vectors)
faiss.write_index(index , "jobs.faiss")

print(f"indexed {len(vectors)} jobs")