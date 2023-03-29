import asyncio
import json
from pathlib import Path
from urllib.parse import unquote_plus

from markupsafe import Markup
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, escape

from articlesa.core.types import SourceNode, SourceTree
from articlesa.logger import logger
import articlesa.front.home
from articlesa.worker import worker


app = FastAPI(title='Article Source Aggregator')


# HOME
app.include_router(articlesa.front.home.router)

# WORKER
app.on_event("startup")(worker.startup)
app.on_event("shutdown")(worker.shutdown)

# ARTICLES
@app.get("/a/{article_url:path}", response_class=HTMLResponse)
async def article(request: Request, article_url: str):
    env = Environment(loader=FileSystemLoader(Path(__file__).parent))
    template = env.get_template('article.html')
    article_url = unquote_plus(article_url)
    return HTMLResponse(template.render(title=f"analysis of {article_url}"))


@app.websocket("/ws/a/{article_url:path}")
async def article_websocket(websocket: WebSocket, depth: int=2):
    await websocket.accept()
    article_url = websocket.path_params['article_url']
    await websocket.send_text("console.log('hello from ws')")

    cleaned_url = await worker.clean_and_add_article(article_url)
    rootarticle = await worker.wait_for_article(cleaned_url)
    root = SourceNode.from_db_article(rootarticle, depth=0)
    root.parsed = True
    tree = SourceTree(root)
    async for tree in await worker.build_tree(tree, depth=depth):
        await websocket.send_text(f"console.log('got tree: {tree}')")
        await websocket.send_text(f"window.tree = {json.dumps(tree)}")

    while True:
        data = await websocket.receive_text()
        logger.info("got command: {}", data)


if __name__ == '__main__':
    print('run me using $ uvicorn articlesa.front.article:app --port 7654 --reload --ws auto --reload-dir articlesa/')
    import uvicorn

    uvicorn.run("articlesa.front.article:app", host="0.0.0.0", port=7654, log_level="info")
