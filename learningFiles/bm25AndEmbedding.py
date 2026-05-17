import numpy as np

"""

a = "purple is the best city in the forest".split()
b = "there is an art to getting your way and throwing bannas on the street is not it".split()
c = "man is an unshaved/uncircumcised big dog in a face mask".split()

# merge all docs into a list of lists to do the cals

docs = [a,b,c]

for i in docs:
    print(i)


def cosine_similarity(a,b):
    a = np.array(a)
    b = np.array(b)

    return np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b))

def tfIdf(word , sentence ,docs):
    tf = sentence.count(word) / len(sentence)

    df=0
    for doc in docs:
        if word in doc:
            df+=1
    if df==0:
        return 0    
    
    idf = np.log(len(docs) / df )

    return round(tf * idf , 4)

#print(tfIdf("forest",a))

# make a vector containing the tfidf of each word in our corpse

vocab = set(a+b+c)
vecs = []
for doc in docs:
    doc_vec = []
    for word in vocab:
        doc_vec.append(tfIdf(word , doc , docs))
    
    vecs.append(doc_vec)


query = "forest city".split()

query_vec = []
for word in vocab:
    query_vec.append(tfIdf(word, query, docs))

scores = []

for vec in vecs:
    score = cosine_similarity(query_vec, vec)
    scores.append(score)

print(scores)
"""

# best match (bm25) 



d = "the black bird flew across the silent river at midnight".split()

e = "computer science students drink coffee while debugging strange errors".split()

f = "ancient kings built massive stone temples near the desert mountains".split()

g = "a lonely astronaut watched the blue earth from deep space".split()

h = "music and poetry can change the mood of an entire city".split()

i = "the hacker quietly wrote code in a dark room full of monitors".split()

docs = [d + e + f + g + h + i]
avgDL = 0
tot=0
for doc in docs:
    tot+=len(doc)
avgDL = tot / len(docs)
n = len(docs)
def bm25(word , sentence , k=1.2 , b=0.75):
    freq = sentence.count(word)
    
    # tf part : ( f(q , d) * (k+1) ) / ( f(t , d) + k * (1 - b + b * (d LEN/all doc LEN AVG) ) :: k=1.25 , b=0.75
    
    tf = (freq * (k+1)) / (freq + k * (1-b+b*(n/avgDL)))

    
    # idf part : log( n - n(q) + 0.5 ) / (n(q) + 0.5) + 1
    
    df=0
    for doc in docs:
        if word in doc:
            df+=1
    if df==0:
        return 0    
    
    idf = np.log( ( (n - df + 0.5) / (df + 0.5) ) + 1 )

    return round(tf * idf , 4)

print(bm25("students" ,e))