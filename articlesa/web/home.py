from pathlib import Path

from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, escape

from articlesa.logger import logger


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def article(request: Request):
    env = Environment(loader=FileSystemLoader(Path(__file__).parent))
    template = env.get_template('article.html')

    logger.info(f"hello from home")

    return HTMLResponse(template.render(title="Article Source Aggregator"))


@router.websocket("/ws/")
async def home_websocket(websocket: WebSocket):
    await websocket.accept()

    logger.info(f"hello from home websocket")

    while True:
        data = await websocket.receive_text()
        logger.info("got command: {}", data)

