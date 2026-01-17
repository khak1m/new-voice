"""
Calendar Tool - проверка доступности и бронирование.

Пример интеграции с внешним календарём.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
import httpx

from .base import Tool, ToolResult, ToolStatus, register_tool


@register_tool
class CalendarTool(Tool):
    """
    Tool для работы с календарём.
    
    Функции:
    - check_availability: проверить доступность времени
    - book_appointment: забронировать встречу
    """
    
    @property
    def name(self) -> str:
        return "calendar"
    
    @property
    def description(self) -> str:
        return "Check calendar availability and book appointments"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["check_availability", "book_appointment"],
                    "description": "Action to perform"
                },
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                },
                "time": {
                    "type": "string",
                    "description": "Time in HH:MM format"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Duration in minutes (default: 60)"
                },
                "service": {
                    "type": "string",
                    "description": "Service name (for booking)"
                },
                "client_name": {
                    "type": "string",
                    "description": "Client name (for booking)"
                },
                "client_phone": {
                    "type": "string",
                    "description": "Client phone (for booking)"
                }
            },
            "required": ["action", "date", "time"]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Выполнить действие с календарём.
        
        Args:
            action: check_availability или book_appointment
            date: Дата (YYYY-MM-DD)
            time: Время (HH:MM)
            duration_minutes: Длительность (по умолчанию 60)
            service: Название услуги (для бронирования)
            client_name: Имя клиента (для бронирования)
            client_phone: Телефон клиента (для бронирования)
            
        Returns:
            ToolResult с результатом
        """
        if not self.validate_params(kwargs):
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Invalid parameters"
            )
        
        action = kwargs.get("action")
        
        if action == "check_availability":
            return await self._check_availability(kwargs)
        elif action == "book_appointment":
            return await self._book_appointment(kwargs)
        else:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Unknown action: {action}"
            )
    
    async def _check_availability(self, params: Dict[str, Any]) -> ToolResult:
        """Проверить доступность времени."""
        date = params.get("date")
        time = params.get("time")
        duration = params.get("duration_minutes", 60)
        
        # Если есть API URL в конфиге, делаем реальный запрос
        api_url = self.config.get("api_url")
        
        if api_url:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{api_url}/availability",
                        params={
                            "date": date,
                            "time": time,
                            "duration": duration
                        },
                        headers=self._get_headers(),
                        timeout=5.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return ToolResult(
                            status=ToolStatus.SUCCESS,
                            data=data,
                            message=f"Availability checked for {date} {time}"
                        )
                    else:
                        return ToolResult(
                            status=ToolStatus.ERROR,
                            error=f"API error: {response.status_code}"
                        )
            
            except Exception as e:
                self.logger.error(f"Calendar API error: {e}")
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=str(e)
                )
        
        # Fallback: mock response
        # В реальности здесь был бы запрос к календарю
        available = True  # Упрощение для MVP
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "available": available,
                "date": date,
                "time": time,
                "duration_minutes": duration
            },
            message=f"Time slot {date} {time} is {'available' if available else 'not available'}"
        )
    
    async def _book_appointment(self, params: Dict[str, Any]) -> ToolResult:
        """Забронировать встречу."""
        date = params.get("date")
        time = params.get("time")
        duration = params.get("duration_minutes", 60)
        service = params.get("service")
        client_name = params.get("client_name")
        client_phone = params.get("client_phone")
        
        # Проверяем обязательные поля для бронирования
        if not all([service, client_name, client_phone]):
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Missing required fields for booking: service, client_name, client_phone"
            )
        
        # Если есть API URL в конфиге, делаем реальный запрос
        api_url = self.config.get("api_url")
        
        if api_url:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{api_url}/appointments",
                        json={
                            "date": date,
                            "time": time,
                            "duration_minutes": duration,
                            "service": service,
                            "client_name": client_name,
                            "client_phone": client_phone
                        },
                        headers=self._get_headers(),
                        timeout=5.0
                    )
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        return ToolResult(
                            status=ToolStatus.SUCCESS,
                            data=data,
                            message=f"Appointment booked for {client_name} on {date} {time}"
                        )
                    else:
                        return ToolResult(
                            status=ToolStatus.ERROR,
                            error=f"API error: {response.status_code}"
                        )
            
            except Exception as e:
                self.logger.error(f"Calendar API error: {e}")
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=str(e)
                )
        
        # Fallback: mock response
        booking_id = f"BOOK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "booking_id": booking_id,
                "date": date,
                "time": time,
                "duration_minutes": duration,
                "service": service,
                "client_name": client_name,
                "client_phone": client_phone,
                "status": "confirmed"
            },
            message=f"Appointment booked successfully. Booking ID: {booking_id}"
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Получить headers для API запросов."""
        headers = {"Content-Type": "application/json"}
        
        api_key = self.config.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        return headers
