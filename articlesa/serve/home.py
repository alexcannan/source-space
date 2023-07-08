"""Informational pages for the site."""
from fastapi import APIRouter, Request


router = APIRouter()


@router.get("/about")
async def about(request: Request) -> dict:
    """Stub for the about page."""
    return {"message": "what are we about?"}
