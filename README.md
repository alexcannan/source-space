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
    Article <|--|> ArticleNode : backend/frontend
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
    class ArticleNode{
        transientId: uuid?
        depth: int
        status: str
    }
    class Link{
        transientId: uuid?
        internal: bool
        from: ArticleNode
        to: ArticleNode
    }
    ArticleTree <|-- ArticleNode : child
    ArticleTree <|-- Link : child
    class ArticleTree{
        root: ArticleNode
        nodes: list[ArticleNode]
        links: list[Link]
        composeMermaid(): str
    }
```


### URLs to test

```
https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/
```
