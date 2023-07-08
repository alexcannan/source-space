"""Handy script to run the server from the command line."""
from pathlib import Path

import uvicorn


uvicorn.run(
    "articlesa.serve:app",
    host="localhost",
    port=7654,
    reload=True,
    reload_dirs=[Path(__file__).parent],
)
