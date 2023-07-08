""" Client-side routes. """
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader


router = APIRouter()


@router.get("/")
async def home() -> HTMLResponse:
    """Return the home page."""
    env = Environment(loader=FileSystemLoader(Path(__file__).parent), autoescape=True)
    template = env.get_template("article.html")
    return HTMLResponse(template.render())
