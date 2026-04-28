from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib.request
import time

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

def get_all_links(page, base_url=""):
    soup = BeautifulSoup(page, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)  # handles relative URLs like /jobs/123
        if urlparse(full_url).scheme in ("http", "https"):
            links.append(full_url)
    return links
    
def union(a,b):
    for i in b:
        if i not in a:
            a.append(i)
    return a


def get_page(url):
    try:
        time.sleep(1.5)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
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
    while toCrawl:
        page = toCrawl.pop()
        if page not in crawled:
            if not can_crawl(page):   # add 
                continue
            content = get_page(page)
            outLinks = get_all_links(content, base_url=page)  # pass page URL here
            union(toCrawl, outLinks)
            graphs[page] = outLinks
            add_page_to_index(Index, page, content)
            crawled.append(page)
    return Index, graphs


import urllib.robotparser

def can_crawl(url):
    try:
        parsed = urlparse(url)
        base = parsed.scheme + "://" + parsed.netloc
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(base + "/robots.txt")
        rp.read()
        return rp.can_fetch("*", url)
    except:
        return True  # if robots.txt can't be read, allow it
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