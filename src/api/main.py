"""
Главный файл API.

Запуск:
    uvicorn src.api.main:app --reload --port 8000
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routers import bots, knowledge_bases, calls, leads, health

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события приложения."""
    print("🚀 NEW-VOICE API запускается...")
    yield
    print("👋 NEW-VOICE API останавливается...")


# Создаём приложение
app = FastAPI(
    title="NEW-VOICE 2.0 API",
    description="API для управления голосовыми AI-ботами",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — разрешаем запросы с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Подключаем роутеры
app.include_router(health.router, tags=["Health"])
app.include_router(bots.router, prefix="/api/bots", tags=["Bots"])
app.include_router(knowledge_bases.router, prefix="/api/knowledge-bases", tags=["Knowledge Bases"])
app.include_router(calls.router, prefix="/api/calls", tags=["Calls"])
app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])


@app.get("/")
async def root():
    """Демо страница."""
    static_dir = Path(__file__).parent / "static"
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "name": "NEW-VOICE 2.0 API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }
