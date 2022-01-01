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

    article_url = unquote_plus(article_url)

    G = recursive_source_check(article_url, max_level=2)
    logger.info(G.nodes(data=True))
    logger.info(G.edges(data=True))

    formatted_nodes = [{"id": k, **v} for k, v in G.nodes(data=True)]
    formatted_edges = [{"source": x[0], "target": x[1], **x[2]} for x in G.edges(data=True)]

    data = f"""{{nodes: {json.dumps(formatted_nodes)}, links: {json.dumps(formatted_edges)}}}"""
    a = f"""
        chart = ForceGraph({data}, {{
            nodeId: d => d.id,
            nodeRadius: d => 5+5+Number(d.scan_depth),
            nodeGroup: d => d.scan_depth,
            nodeTitle: d => `${{d.id}}\n${{d.group}}`,
            nodeStrength: 0.1,
            linkStrokeWidth: l => Math.sqrt(1),
            linkStrength: 1e-3,
            width: window.screen.width,
            height: window.screen.height
        }});
        document.body.appendChild(chart);
    """
    logger.info(f"sending {a}")
    await websocket.send_text(a)

    while True:
        data = await websocket.receive_text()
        logger.info("got command: {}", data)


if __name__ == '__main__':
    print('run me using $ uvicorn articlesa.web.article:app --port 7654 --reload --ws auto --reload-dir articlesa/')
    import uvicorn

    uvicorn.run("articlesa.web.article:app", host="0.0.0.0", port=7654, log_level="info")
