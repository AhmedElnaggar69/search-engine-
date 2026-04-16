

"""
def palindromes(s):
    if s == "":
        return True
    else :
        if s[0] == s[-1] :

            return palindromes(s[1:-1])
        else:
            return False
        
print(palindromes('noon' ))
"""

"""
def fib(n):
    val = 0
    prev = 0
    prevPrev = 1
    while val < n:
        res = prev + prevPrev
        prevPrev = prev
        prev = res
        val+=1
    return res
print(fib(33))
print(fib(60))
"""




import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

start_link = '<a href="'
def add_to_index(index , keyword , url):
    if keyword in  index:
       index[keyword].append(url)
    else:
        index[keyword] = [url]

def lookup(index , keyword):
    if keyword in index:
        return index[keyword]
    return None

def get_all_links(page):
    links = []
    while True:
        startPhase = page.find(start_link)

        if startPhase == -1:   
            break

        startOfLinkNum = startPhase + len(start_link)   
        endOfLink=page.find('"' ,startOfLinkNum )

        if(endOfLink==-1):
            break
    
        link = page[startOfLinkNum : endOfLink]

        links.append(link)
        page = page[endOfLink+1:]
    return links
    
def union(a,b):
    for i in b:
        if i not in a:
            a.append(i)
    return a

import urllib.request

def get_page(url):
    try:
        return urllib.request.urlopen(url).read().decode('utf-8', errors='ignore')
    except:
        return ""


def add_page_to_index(index , url , page):
    cleanRes = cleaning(page)
    for word in cleanRes:
        add_to_index(index , word , url)

def cleaning(page):
    words = re.findall(r'\b\w+\b', page.lower())
    
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    
    res = []

    for word in words:
        if word not in stop_words:
            lemma =  lemmatizer.lemmatize(word , pos='v')
            res.append(lemma)
    
    return res




def crawl_web(seed):
    toCrawl = [seed]
    crawled = []
    Index = {}
    graphs = {}
    while toCrawl :
        #dfs for now
        page = toCrawl.pop()
        if page not in crawled :
            # append here is not correct for toCrawl
            content = get_page(page)
            outLinks = get_all_links(content)
            union(toCrawl,outLinks)

            graphs[page] = outLinks
            add_page_to_index(Index , page , content)
            crawled.append(page)
    return Index , graphs

def compute_ranks(graph):
    dampingF = 0.85
    numLoops = 10

    ranks = {}
    npages = len(graph)

    for page in graph:
        ranks[page] = 1.0 / npages

    for i in range(numLoops):
        newRanks = {}
        for page in graph:
            newRank = (1 - dampingF) / npages

            for node in graph:
                if page in graph[node] and len(graph[node]) > 0:
                    newRank += dampingF * (ranks[node] / len(graph[node]))

            newRanks[page] = newRank

        ranks = newRanks

    return ranks