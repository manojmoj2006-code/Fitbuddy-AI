"""FitBuddy application entry point. Run with: uvicorn app.main:app --reload"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import config, database
from app.routes import router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    if not config.GEMINI_API_KEY:
        logging.getLogger("fitbuddy").warning(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    yield


app = FastAPI(title="FitBuddy - AI Fitness Plan Generator", lifespan=lifespan)
config.STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
app.include_router(router)
