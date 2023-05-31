from fastapi import FastAPI

from articlesa.serve.client import router as client_router
from articlesa.serve.gateway import router as gateway_router
from articlesa.serve.home import router as home_router


app = FastAPI()

app.include_router(client_router)
app.include_router(gateway_router)
app.include_router(home_router)


if __name__ == '__main__':
    print('run me using $ uvicorn articlesa.serve:app --port 7654 --reload --ws auto --reload-dir articlesa/')
    import uvicorn

    uvicorn.run("articlesa.front.article:app", host="0.0.0.0", port=7654, log_level="info")
