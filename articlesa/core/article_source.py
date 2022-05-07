from typing import Union
from urllib.parse import urlunparse, urlparse

import networkx as nx
from yarl import URL

from .source_node import SourceNode
from .types import clean_url


class ArticleSource():
    url: URL
    G: nx.DiGraph

    def __init__(self, url: Union[str, URL]):
        self.url = URL(clean_url(url))
        self.G = nx.DiGraph()
        self.G.add_node(self.url,
                        scan_depth=0,
                        parsed=False,
                        pos=[0, 0],
                        domain=self.url.host)

    def recursive_source_check(self, max_level=3):
        self.G = self.get_sources(self.G, clean_url(url))
        while any(x < max_level for x in get_leaf_depths(G)):
            urls = [x for x in G.nodes() if G.nodes[x]["parsed"] == False]
            G = self.get_sources(G, clean_url(urls[0]))
        return G

    def get_sources(G, node_url):
        new_depth = G.nodes[node_url]["scan_depth"] + 1
        node = SourceNode(node_url)
        node.get_links()
        node.filter_links(check_blacklist=True, ignore_local=False)
        for i, link in enumerate(node.links):
            if clean_url(link) not in G:
                G.add_node(clean_url(link),
                        scan_depth=new_depth,
                        parsed=False,
                        pos=[new_depth,
                                count_articles_at_depth(G, new_depth)],
                        domain=get_domain(link)
                        )
            G.add_edge(node_url, clean_url(link))
        G.nodes[node_url]["parsed"] = True
        return G


def count_articles_at_depth(G, d):
    """ Counts number of articles at a certain depth """
    return len([x for x in G.nodes if G.nodes[x]["scan_depth"] == d])


def get_leaf_depths(G):
    leaves = [G.nodes[x]["scan_depth"] for x in G.nodes()
              if G.nodes[x]["parsed"] == False]
    return leaves





def source_tree_report(G):
    """ Reports various information about source tree """
    # TODO: Get most cited articles, maybe run domains through
    #       a web credibility project
    # Get most referenced articles
    ref_dict = {}
    for node in G.nodes:
        ref_dict[node] = G.in_degree[node]
    most_refd = max(ref_dict.items(), key=operator.itemgetter(1))[0]
    print("Most referenced article:", most_refd)
    print("With", ref_dict[most_refd], "citations")
    return ref_dict


def save_source_tree(G):
    nx.write_gpickle(G, "source_tree.pickle")


if __name__ == '__main__':
    G = recursive_source_check(url, max_level=3)
    save_source_tree(G)
    # draw_source_tree_matplotlib(G)
    r = source_tree_report(G)
