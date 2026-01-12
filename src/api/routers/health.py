"""Health check эндпоинты."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Проверка здоровья API."""
    return {"status": "healthy"}


@router.get("/health/detailed")
async def detailed_health():
    """Детальная проверка всех сервисов."""
    from src.database.connection import check_connection
    
    services = {
        "api": "healthy",
        "database": "unknown",
        "qdrant": "unknown",
    }
    
    # Проверяем PostgreSQL
    try:
        if check_connection():
            services["database"] = "healthy"
        else:
            services["database"] = "unhealthy"
    except Exception as e:
        services["database"] = f"error: {str(e)}"
    
    # Проверяем Qdrant
    try:
        from qdrant_client import QdrantClient
        import os
        
        client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
        )
        client.get_collections()
        services["qdrant"] = "healthy"
    except Exception as e:
        services["qdrant"] = f"error: {str(e)}"
    
    # Общий статус
    all_healthy = all(v == "healthy" for v in services.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services,
    }
