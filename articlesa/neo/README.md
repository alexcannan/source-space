# articlesa.neo

## Cypher Syntax

Cypher has nodes and relationships articlesa can use. This document is hopefully a quick guide to bring whoever is working with articlesa up to speed.

### Entities

#### Article

Represents an article.
It has properties identical to the ParsedArticle type, minus the transcript.
It has labels based on the netloc, which is a proxy for which site the article came from.

#### Author

Represents an author.
It simply has a name property.
Relationships are created from articles to authors, in order to track authorship across the graph.

### Example queries

#### Create an article and author node given a ParsedArticle

```cypher
MERGE (article:Article {url: $url})
SET article.title = $title,
    article.links = $links,
    article.published = $published,
    article.parsedAtUtc = $parsedAtUtc
WITH article
UNWIND $authors AS author_name
MERGE (author:Author {name: author_name})
MERGE (article)-[:AUTHORED_BY]->(author)
```

#### Get article that matches url

```cypher
MATCH (article:Article {url: $url})
RETURN article
```
