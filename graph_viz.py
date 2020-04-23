"""
Author: Alex Cannan
Date Created: 4/23/20
Purpose: This file will contain methods to visualize the source tree using
graphviz
"""

from graphviz import Digraph


def export_tree(head_node, depth=3):
    u = Digraph('Source Tree', filename='article-source-tree.gv',
            node_attr={'color': 'lightblue2', 'style': 'filled'})
    u.attr(size='6,6')

    d = 0
    while d < depth:
        # TODO: figure out how to get all nodes at a certain depth
        d += 1

u = Digraph('Source Tree', filename='article-source-tree.gv',
            node_attr={'color': 'lightblue2', 'style': 'filled'})
u.attr(size='6,6')

u.edge('5th Edition', '6th Edition')
u.edge('5th Edition', 'PWB 1.0')
u.edge('6th Edition', 'LSX')


u.view()