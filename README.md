# article-source-aggregator

Build a source tree from a news article recursively

```
source setup.sh
python3 -m articlesa.front.article
```


## Data Structures

```mermaid
---
title: Article Source Aggregator
---
classDiagram
    Article <|--|> SourceNode : backend/frontend
    class Article{
        mongoId: ObjectId
        url: str
        urlHash: b64 str
        text: str
        hits: int
        allParents: set[Article]
        allChildren: set[Article]
        fromUrl(url: str): Article
    }
    class SourceNode{
        transientId: uuid?
        depth: int
        status: str
    }
    class Link{
        transientId: uuid?
        internal: bool
        from: SourceNode
        to: SourceNode
    }
    SourceTree <|-- SourceNode : child
    SourceTree <|-- Link : child
    class SourceTree{
        root: SourceNode
        nodes: list[SourceNode]
        links: list[Link]
        composeMermaid(): str
    }
```

## Displaying the tree

SourceNodes are nodes on a graph. Links are edges on a graph.

SourceTree goes left to right, depth levels are TB subgraphs.

```mermaid
graph LR
    A[Article] --> B[SourceNode]
    B --> C[SourceTree]
    C --> D[SourceNode]
    C --> E[Link]
    D --> F[SourceNode]
    E --> G[SourceNode]
    E --> H[SourceNode]
```

### URLs to test

```
https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/
```
