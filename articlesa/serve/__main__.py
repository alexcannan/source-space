"""Handy script to run the server from the command line."""
from pathlib import Path

import uvicorn

from articlesa.config import ServeConfig


uvicorn.run(
    "articlesa.serve:app",
    host="localhost",
    port=ServeConfig.port,
    reload=True,
    reload_dirs=[str(Path(__file__).parent)],
)
