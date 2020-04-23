from pprint import pprint
from urllib.parse import urlparse

from newspaper import Article

url = 'https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/'

blacklist = [
    "google.com",
    "twitter.com",
]

def get_url_base(url):
    return urlparse(url).netloc


def get_article_links(article_url, ignore_local=True):
    article_url_base = get_url_base(article_url)
    article = Article(url=article_url)
    article.download()
    article.parse()
    links = article.links
    good_links = []
    for link in links:
        link_good = True
        base = get_url_base(link)
        if ignore_local and base == article_url_base:
            link_good = False
        for badurl in blacklist:
            if badurl in base:
                link_good = False
        if base == '':
            link_good = False
        if link_good:
            good_links.append(link)
    return good_links


def recursive_source_check(url, max_level=5):
    i = 0
    sources = {url: {}}
    next_visit = [url]
    while i < max_level:
        print("Searching up to layer", i)
        visiting = next_visit
        next_visit = []
        for a in visiting:
            links = get_article_links(a)
            sources[a] = links
            next_visit += links
        i += 1
        pprint(sources)



if __name__ == '__main__':
    recursive_source_check(url)
