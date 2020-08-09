from pprint import pprint
from urllib.parse import urlparse, urlunparse

import networkx as nx
from newspaper import Article

from source_node import SourceNode

url = 'https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/'


def clean_url(url):
    return urlunparse(urlparse(url))


def get_leaf_depths(G):
    leaves = [G.nodes[x]["scan_depth"] for x in G.nodes()
              if G.nodes[x]["parsed"] == False]
    return leaves


def get_sources(G, node_url):
    new_depth = G.nodes[node_url]["scan_depth"] + 1
    node = SourceNode(node_url)
    node.get_links()
    node.filter_links()
    for link in node.links:
        G.add_node(clean_url(link),
                   scan_depth=new_depth,
                   parsed=False)
        G.add_edge(node_url, clean_url(link))
    G.nodes[node_url]["parsed"] = True
    return G


def recursive_source_check(url, max_level=5):
    G = nx.DiGraph()
    G.add_node(clean_url(url), scan_depth=0)
    G = get_sources(G, clean_url(url))
    while any(x < max_level for x in get_leaf_depths(G)):
        urls = [x for x in G.nodes() if G.nodes[x]["parsed"] == False]
        G = get_sources(G, clean_url(urls[0]))
    return G



def draw_source_tree(G):
    import matplotlib.pyplot as plt
    nx.draw_shell(G, with_labels=True)
    plt.show()


if __name__ == '__main__':
    G = recursive_source_check(url)
    draw_source_tree(G)
