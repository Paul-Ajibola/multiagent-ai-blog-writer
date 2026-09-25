from __future__ import annotations


import uvicorn

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from web.config import IMAGES_DIR, STATIC_DIR
from web.routes import agent, downloads, health, pages

app = FastAPI(
    title="LangGraph Blog Agent",
    description="FastAPI frontend for the existing LangGraph workflow.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

app.include_router(pages.router)
app.include_router(health.router)
app.include_router(agent.router)
app.include_router(downloads.router)



if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)



