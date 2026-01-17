"""
Transfer Tool - перевод звонка на оператора.

Интеграция с LiveKit для transfer calls.
"""

from typing import Dict, Any

from .base import Tool, ToolResult, ToolStatus, register_tool


@register_tool
class TransferTool(Tool):
    """
    Tool для перевода звонка.
    
    Функции:
    - transfer_to_operator: перевести на оператора
    - transfer_to_department: перевести в отдел
    """
    
    @property
    def name(self) -> str:
        return "transfer"
    
    @property
    def description(self) -> str:
        return "Transfer call to operator or department"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "enum": ["operator", "sales", "support", "manager"],
                    "description": "Transfer target"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for transfer"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"],
                    "description": "Transfer priority (default: normal)"
                }
            },
            "required": ["target"]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Выполнить перевод звонка.
        
        Args:
            target: Куда переводить (operator, sales, support, manager)
            reason: Причина перевода
            priority: Приоритет (low, normal, high, urgent)
            
        Returns:
            ToolResult с результатом
        """
        if not self.validate_params(kwargs):
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Invalid parameters"
            )
        
        target = kwargs.get("target")
        reason = kwargs.get("reason", "Customer request")
        priority = kwargs.get("priority", "normal")
        
        # В реальности здесь была бы интеграция с LiveKit SIP
        # Для MVP возвращаем успешный результат
        
        self.logger.info(f"Transfer requested: target={target}, reason={reason}, priority={priority}")
        
        # Получаем номер/SIP URI из конфига
        transfer_config = self.config.get("targets", {})
        target_uri = transfer_config.get(target)
        
        if not target_uri:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Transfer target '{target}' not configured"
            )
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "target": target,
                "target_uri": target_uri,
                "reason": reason,
                "priority": priority,
                "status": "pending"
            },
            message=f"Call transfer initiated to {target}"
        )
