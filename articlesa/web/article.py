import asyncio
import json
from pathlib import Path
from urllib.parse import unquote_plus

from markupsafe import Markup
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, escape

from articlesa.logger import logger

from articlesa.core.find_source import recursive_source_check
import articlesa.web.home


app = FastAPI(title='Article Source Aggregator')

app.include_router(articlesa.web.home.router)


@app.get("/a/{article_url:path}", response_class=HTMLResponse)
async def article(article_url: str, request: Request, depth: int=2):
    env = Environment(loader=FileSystemLoader(Path(__file__).parent))
    template = env.get_template('article.html')

    article_url = unquote_plus(article_url)

    return HTMLResponse(template.render(title=f"analysis of {article_url}"))


@app.websocket("/ws/a/{article_url:path}")
async def article_websocket(websocket: WebSocket):
    # TODO: why isn't this being entered?
    await websocket.accept()
    article_url = websocket.path_params['article_url']

    websocket.send_text("console.log('hello from ws')")

    article_url = unquote_plus(article_url)

    G = recursive_source_check(article_url, max_level=2)
    logger.info(G.nodes)
    logger.info(G.edges)

    websocket.send_text(f"""
        chart = ForceGraph(nodes: {json.dumps([G.nodes])}, edges: {json.dumps([G.edges])})
    """)

    while True:
        data = await websocket.receive_text()
        logger.info("got command: {}", data)


if __name__ == '__main__':
    print('run me using $ uvicorn articlesa.web.article:app --port 7654 --reload --ws auto --reload-dir articlesa/')
    import uvicorn

    uvicorn.run("articlesa.web.article:app", host="0.0.0.0", port=7654, log_level="info")
