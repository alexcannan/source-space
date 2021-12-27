import argparse

from articlesa.find_source import recursive_source_check
from articlesa.visualize import draw_source_tree_graphviz


parser = argparse.ArgumentParser(description="\
    articlesa generates a source tree from online articles by analyzing links within the article body.\
        ")
parser.add_argument("--url", "-u", type=str, help="url of article to be analyzed")
parser.add_argument("--depth", "-d", type=int, default=3, help="depth of recursive source retrieval")
args = parser.parse_args()

G = recursive_source_check(args.url, max_level=args.depth)
draw_source_tree_graphviz(G)