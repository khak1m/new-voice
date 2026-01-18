"""
Главный файл API для ПРОДАКШЕНА.

Этот файл настроен для раздачи собранного фронтенда.

Запуск:
    uvicorn src.api.main_production:app --host 0.0.0.0 --port 8000
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routers import bots, knowledge_bases, calls, leads, health, dashboard, skillbases, campaigns, analytics

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события приложения."""
    print("🚀 NEW-VOICE API запускается (PRODUCTION MODE)...")
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

# Подключаем роутеры API
app.include_router(health.router, tags=["Health"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(bots.router, prefix="/api/bots", tags=["Bots"])
app.include_router(knowledge_bases.router, prefix="/api/knowledge-bases", tags=["Knowledge Bases"])
app.include_router(calls.router, prefix="/api/calls", tags=["Calls"])
app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
app.include_router(skillbases.router, prefix="/api/skillbases", tags=["Skillbases"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


# Раздача собранного фронтенда (ДОЛЖНО БЫТЬ ПОСЛЕДНИМ!)
frontend_dist = Path(__file__).parent.parent.parent / "frontend-dist"

if frontend_dist.exists():
    print(f"✅ Фронтенд найден: {frontend_dist}")
    
    # Раздаем статические файлы (JS, CSS, изображения)
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    # Раздаем index.html для всех остальных путей (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Раздает index.html для всех путей (кроме /api)."""
        # Если путь начинается с /api, пропускаем (обрабатывается роутерами)
        if full_path.startswith("api/"):
            return {"error": "Not found"}
        
        # Проверяем, существует ли файл
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        # Иначе возвращаем index.html (для SPA routing)
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        
        return {"error": "Frontend not found"}
else:
    print(f"⚠️  Фронтенд не найден: {frontend_dist}")
    print("   Запустите: npm run build в папке new-voice-frontend")
    print("   И загрузите dist/ в папку frontend-dist/")
    
    @app.get("/")
    async def root():
        """Демо страница (когда фронтенд не собран)."""
        return {
            "name": "NEW-VOICE 2.0 API",
            "version": "2.0.0",
            "status": "running",
            "docs": "/docs",
            "warning": "Frontend not deployed. Build and deploy frontend to see the UI.",
        }
