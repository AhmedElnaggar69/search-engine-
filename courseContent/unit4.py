import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

start_link = '<a href="'
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

def crawl_web(seed):
    toCrawl = [seed]
    crawled = []
    Index = []
    while toCrawl :
        #dfs for now
        page = toCrawl.pop()
        if page not in crawled :
            # append here is not correct for toCrawl
            #content = get_page(page)
            #union(toCrawl,get_all_links(content))

            # add page to index for each content(str) in each page

            # add_page_to_inedx(Index , page , content)
            crawled.append(page)
    return Index


Index = []

def record_user_click(index , keyword , url):
    urls = lookup(index , keyword)
    if urls:
        for entry in urls:
            if(entry[0]==url):
                entry[1] = entry[1] + 1
                

def add_to_index(index , keyword , url):
    for entry in index :
        
        if entry[0]==keyword:
            # keyword already exists
            if url not in entry[1]:
                # url and count for basic ranking
                entry[1].append([url,0])
                return
    index.append([keyword , [url]])


"""
add_to_index(Index, "black", "buyslaves2026.com")
add_to_index(Index, "black", "slaves2026.com")
add_to_index(Index, "python", "docs.python.org")
add_to_index(Index, "ai", "openai.com")
add_to_index(Index, "search", "google.com")
add_to_index(Index, "python", "python.com")
add_to_index(Index, "sports", "football.org")
add_to_index(Index, "ai", "deepmind.com")
add_to_index(Index, "love", "tinder.com")
add_to_index(Index, "love", "grindr.com")
add_to_index(Index, "data", "numpy.org")
add_to_index(Index, "python", "pypi.org")

for entry in Index:
    print(str(entry[0]) + " -> " + str(entry[1]))
"""

def lookup(index , keyword):
    for entry in index :
        if entry[0]==keyword:
            return entry[1]
    # none found 
    return []

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


add_page_to_index(Index, "fake.test", "this is a test")
add_page_to_index(Index, "news.site", "Breaking news about Python programming")
add_page_to_index(Index, "blog.ai", "AI is changing the world")
add_page_to_index(Index, "sports.zone", "Football and basketball updates")
add_page_to_index(Index, "recipes.com", "Easy recipes for healthy meals")
add_page_to_index(Index, "tech.blog", "New AI tools and Python tutorials")
add_page_to_index(Index, "funStuff.site", "Funny memes and stuff online yibbi")
add_page_to_index(Index, "shop.com", "Buy smart devices and gadgets")
add_page_to_index(Index, "slaveMarket.com", "Buy smart slaves")
add_page_to_index(Index, "data.org", "Data analysis with Python and Pandas")
add_page_to_index(Index, "education.site", "Learning resources for AI and coding")

#for entry in Index:
#    print(str(entry[0]) + " -> " + str(entry[1]))

k = "buy"
print("the key word ("+ k + ") appers in the following pages -> " + str(lookup(Index , "buy")))


# magic get page for our crawler (for now)
def get_page(url):
    try:
        import urllib
        return urllib.urllib.urlopen(url).read()
    except:
        return ""