# article-source-aggregator

Build a source tree from a news article recursively

```
source setup.sh
python3 -m articlesa.front.article
```

## architecture

```mermaid
sequenceDiagram
    participant client
    participant server
    participant db
    participant worker
    participant web
    client ->> server: GET /a/{article:path}
    server ->> server: clean url
    server ->> db: check if article exists and is not old
    alt article exists and is not old
        db -->> server: retrieve article
    else article doesn't exist or is old
        db -->> server: article doesn't exist
        server ->> worker: send article to worker
        worker ->> web: GET article
        web ->> worker: return article and parse
        worker ->> db: save article
        server -->> db: poll for article
        db -->> server: retrieve article
    end
    server ->> client: send article node event for rendering
    alt depth reached
        server ->> client: end stream
    else depth not reached
        server ->> server: parse links from last article node
        server ->> server: GOTO clean url
    end


```

### URLs to test

```
https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/
```
