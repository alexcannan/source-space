"""
Author: Alex Cannan
Date Created: 9/24/20
Purpose: This module will contain methods to visualize the source tree.
"""

import networkx as nx


def draw_source_tree_matplotlib(G):
    """ Displays graph using networkx's matplotlib bindings """
    import matplotlib.pyplot as plt
    # Create position dict
    pos = {}
    for node in G.nodes:
        pos[node] = G.nodes[node]["pos"]
    # Create label dict
    labels = {}
    for node in G.nodes:
        labels[node] = G.nodes[node]["domain"]
    nx.draw_networkx(G, with_labels=True, labels=labels, pos=pos)
    plt.show()


# TODO: Create new drawing function that uses graphviz, networkx has bindings
#       to create AGraph, see networkx.drawing.nx_agraph.to_agraph

def draw_source_tree_graphviz(G):
    """ Displays graph using networkx's graphviz bindings """
    rename_mapping = {}
    for node in G.nodes:
        G.nodes[node]["url"] = node
        domain = G.nodes[node]["domain"]
        while domain in rename_mapping.values():
            domain += "+"
        rename_mapping[node] = domain
    G = nx.relabel_nodes(G, rename_mapping)
    a = nx.nx_agraph.to_agraph(G)
    print(a)
    a.layout(prog="dot")
    # TODO: Figure out how to draw extra data & use title and domain
    #       as main info
    a.draw("source_tree.png")
    return a

if __name__ == '__main__':
    G = nx.read_gpickle("source_tree.pickle")
    a = draw_source_tree_graphviz(G)
