from typing import Union

import networkx as nx
from yarl import URL

from .source_node import SourceNode
from .types import clean_url


class ArticleSource():
    """
    ArticleSource is a class that takes a URL and generates a networkx graph of which other articles are
    referenced by the article. This is useful for finding the primary source of an article, or finding the
    most referenced articles.
    """
    url: URL
    G: nx.DiGraph

    def __init__(self, url: Union[str, URL]):
        self.url = clean_url(url)
        self.G = nx.DiGraph()
        self.G.add_node(self.url,
                        scan_depth=0,
                        parsed=False,
                        pos=[0, 0],
                        domain=URL(self.url).host)

    def _count_articles_at_depth(self, d):
        """ counts number of articles at a certain depth. useful for assigning a unique position to each node """
        return len([x for x in self.G.nodes if self.G.nodes[x]["scan_depth"] == d])


    def _get_leaf_depths(self):
        leaves = [self.G.nodes[x]["scan_depth"] for x in self.G.nodes() if self.G.nodes[x]["parsed"] == False]
        return leaves

    def recursive_source_check(self, max_level=3):
        self.get_sources(clean_url(url))
        while any(x < max_level for x in self._get_leaf_depths()):
            urls = [x for x in self.G.nodes() if self.G.nodes[x]["parsed"] == False]
            self.get_sources(clean_url(urls[0]))

    def get_sources(self, node_url):
        new_depth = self.G.nodes[node_url]["scan_depth"] + 1
        node = SourceNode(node_url)
        node.get_links()
        node.filter_links(check_blacklist=True, ignore_local=False)
        for link in node.links:
            cleaned_link = clean_url(link)
            if cleaned_link not in self.G:
                self.G.add_node(cleaned_link,
                        scan_depth=new_depth,
                        parsed=False,
                        pos=[new_depth, self._count_articles_at_depth(new_depth)],
                        domain=URL(link).host,
                        )
            self.G.add_edge(node_url, cleaned_link)
        self.G.nodes[node_url]["parsed"] = True

    def print_report(self):
        """ Reports various information about source tree """
        # TODO: Get most cited articles, maybe run domains through
        #       a web credibility project
        # Get most referenced articles
        ref_dict = {}
        for node in self.G.nodes:
            ref_dict[node] = self.G.in_degree[node]
        most_refd = max(ref_dict.items(), key=lambda x: x[1])[0]
        print("Most referenced article:", most_refd)
        print("With", ref_dict[most_refd], "citations")
        return ref_dict

    def save(self, filename: str="source_tree.pickle"):
        nx.write_gpickle(self.G, filename)


if __name__ == '__main__':
    url = "https://www.nytimes.com/2022/11/02/us/politics/biden-speech-democracy-election.html"
    source = ArticleSource(url)
    source.recursive_source_check(max_level=3)
    source.print_report()