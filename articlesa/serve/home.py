from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader

from articlesa.logger import logger


router = APIRouter()


@router.get("/about")
async def about(request: Request):
    return {"message": "what are we about?"}
