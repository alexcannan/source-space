import asyncio
from pathlib import Path

from markupsafe import Markup
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from jinja2 import Template, Environment, FileSystemLoader, escape

from articlesa.logger import logger

import articlesa.web.home

app = FastAPI(title='Article Source Aggregator')

app.include_router(articlesa.web.home.router)

@app.get("/a/{article_url}", response_class=HTMLResponse)
async def clip(article_url: str, request: Request):
    env = Environment(loader=FileSystemLoader(Path(__file__).parent))
    template = env.get_template('article.html')

    return HTMLResponse(template.render(title=request.url.path[1:]))


@app.websocket("/ws/{article_url}")
async def clip_websocket(websocket: WebSocket):
    await websocket.accept()
    article_url = websocket.path_params['article_url']

    while True:
        data = await websocket.receive_text()
        logger.info("got command: {}", data)


if __name__ == '__main__':
    print('run me using $ uvicorn articlesa.web.article:app --port 7654 --reload --ws auto --reload-dir articlesa/')
    import uvicorn

    uvicorn.run("articlesa.web.article:app", host="0.0.0.0", port=7654, log_level="info")
