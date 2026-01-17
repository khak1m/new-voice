"""
Function calling tools для Skillbase.

Инструменты позволяют боту выполнять действия:
- Проверять доступность в календаре
- Бронировать встречи
- Переводить звонки
- Отправлять SMS/Email
"""

from .base import Tool, ToolResult, ToolRegistry
from .calendar_tool import CalendarTool
from .transfer_tool import TransferTool

__all__ = [
    "Tool",
    "ToolResult",
    "ToolRegistry",
    "CalendarTool",
    "TransferTool",
]
