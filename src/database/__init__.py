"""
Database module for NEW-VOICE 2.0.

Модуль для работы с PostgreSQL через SQLAlchemy.
"""

from .connection import get_db, get_async_db, init_db
from .models import (
    Company,
    User,
    Bot,
    KnowledgeBase,
    Document,
    Call,
    Message,
    Lead,
    Webhook,
)

__all__ = [
    # Connection
    "get_db",
    "get_async_db", 
    "init_db",
    # Models
    "Company",
    "User",
    "Bot",
    "KnowledgeBase",
    "Document",
    "Call",
    "Message",
    "Lead",
    "Webhook",
]
