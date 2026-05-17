import pickle
import pandas as pd
import numpy as np
import faiss
import sys
import os
from sentence_transformers import SentenceTransformer
from preprocess import preprocess

# Paths relative to code/ (cwd when called from main.py)
with open("bm25_title.pkl", "rb") as f:
    bm25_title = pickle.load(f)

with open("bm25_full.pkl", "rb") as f:
    bm25_full = pickle.load(f)

df          = pd.read_pickle("data/jobs.pkl")
faiss_index = faiss.read_index("jobs.faiss")
model       = SentenceTransformer('all-MiniLM-L6-v2')


def search(query, top_k=20):
    tokens = preprocess(query)
    n      = len(df)

    title_scores  = bm25_title.get_scores(tokens)
    full_scores   = bm25_full.get_scores(tokens)
    bm25Combined  = 0.4 * title_scores + 0.6 * full_scores
    bm25Norm      = bm25Combined / (bm25Combined.max() + 1e-9)

    q_vec              = model.encode([query])
    distance, indx     = faiss_index.search(q_vec, n)
    sem_scores         = np.zeros(n)
    for rank, idx in enumerate(indx[0]):
        sem_scores[idx] = 1 - (rank / n)

    finalScore  = 0.4 * bm25Norm + 0.6 * sem_scores
    top_indices = finalScore.argsort()[::-1][:top_k]

    results          = df.iloc[top_indices][['title', 'company', 'url', 'job_type']].copy()
    results['score'] = finalScore[top_indices].round(4)
    return results


if __name__ == "__main__":
    # Called directly or via main.py subprocess:
    #   python search.py "software engineer" 10
    query  = sys.argv[1] if len(sys.argv) > 1 else "intern"
    top_k  = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    print(f"\nQuery: '{query}'  (top {top_k})\n")
    results = search(query, top_k=top_k)
    print(results.to_string(index=False))