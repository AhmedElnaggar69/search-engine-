import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

start_link = '<a href="'



"""
import time
# time.clock is no longer used and we don't need eval

def exec_time(code):
    start = time.perf_counter()
    res = code

    runTime = time.perf_counter() - start
    return res , runTime

def takeAhike(n):
    i=0
    while(i<n):
        i+=1

print(exec_time(takeAhike(10**8))[1] * (10**-7))
"""


"""
# dan bernstein hash
def hash_string(listOfStrings , bucketsNum):
    hashTable = [[] for _ in range(bucketsNum)]
    for s in listOfStrings:
        h = 5381
        for c in s:
            h = (h * 33) + ord(c)
        hashTable[(h%bucketsNum)].append(s)
    return hashTable
table = hash_string(["man","no man is safe","im goin to kill u safe" , '2',"aspodaspdok","woman" , "child" , "child" , "total" , "car"] , 50)

#for i in table:
#    print(i)
"""


# custom hash table
def hash_string(keyword , bucketsNum):
    h = 0
    for c in keyword:
        h = (h + ord(c) ) % bucketsNum
    return h

def hashtable_get_bucket(htable , key):
    return htable[hash_string(key , len(htable))]

def make_hashtable(nBuckets):
    table = [ [] for _ in range(0,nBuckets)]
    return table

def hashtable_lookup(htable , key):
    bucket = hashtable_get_bucket(htable , key)
    for entry in bucket:
        if entry[0] == key:
             return entry[1]
    return None

def hashTable_update(htable , key ,val):
    bucket = hashtable_get_bucket(htable , key)
    for entry in bucket:
        if entry[0] == key:
            entry[1] = val
            return
    bucket.append([key , val])
"""
table = make_hashtable(3)
hashTable_update(table,"udacity" , 23)
hashTable_update(table,"audacity" , 17)
hashTable_update(table,"bodacity" , 69)
hashTable_update(table,"udacity" , 54)
print(hashtable_lookup(table , "udacity"))
"""



# changes only in add_to_index with the rest of the code
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

def get_page(url):
    try:
        import urllib
        return urllib.urllib.urlopen(url).read()
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
    while toCrawl :
        #dfs for now
        page = toCrawl.pop()
        if page not in crawled :
            # append here is not correct for toCrawl
            content = get_page(page)
            union(toCrawl,get_all_links(content))

            # add page to index for each content(str) in each page

            add_page_to_index(Index , page , content)
            crawled.append(page)
    return Index






 