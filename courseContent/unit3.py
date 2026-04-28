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
