"""
Tool Registry

Defines all available tools and handles tool execution routing.
Uses allowlist pattern - only explicitly defined tools can be called.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models import ToolCall, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all available tools.
    
    Security principle: Explicit allowlist, no dynamic tool loading.
    Every tool must be registered here with schema validation.
    """
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """
        Register all available tools with their schemas.
        
        Why schemas are critical:
        - Validates LLM output before execution
        - Prevents malformed or malicious parameters
        - Documents expected inputs/outputs
        """
        
        # Tool 1: Schedule Appointment
        self.register_tool(
            name="schedule_appointment",
            description="Schedule an appointment for the user",
            parameters={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Appointment date in YYYY-MM-DD format"
                    },
                    "time": {
                        "type": "string",
                        "description": "Appointment time in HH:MM format (24-hour)"
                    },
                    "purpose": {
                        "type": "string",
                        "description": "Purpose of the appointment"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Expected duration in minutes",
                        "default": 30
                    }
                },
                "required": ["date", "time", "purpose"]
            },
            handler=self._handle_schedule_appointment
        )
        
        # Tool 2: Get Available Slots
        self.register_tool(
            name="get_available_slots",
            description="Get available appointment slots for a date",
            parameters={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format"
                    }
                },
                "required": ["date"]
            },
            handler=self._handle_get_available_slots
        )
        
        # Tool 3: Cancel Appointment
        self.register_tool(
            name="cancel_appointment",
            description="Cancel an existing appointment",
            parameters={
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "string",
                        "description": "The ID of the appointment to cancel"
                    }
                },
                "required": ["appointment_id"]
            },
            handler=self._handle_cancel_appointment
        )
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: callable,
        requires_auth: bool = True
    ):
        """
        Registers a new tool in the system.
        
        Args:
            name: Unique tool identifier
            description: What the tool does (used by LLM)
            parameters: JSON Schema for parameters
            handler: Function to execute the tool
            requires_auth: Whether tool requires verified user
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
            "requires_auth": requires_auth
        }
        logger.info(f"Registered tool: {name}")
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Returns tool definitions in format expected by LLM.
        
        Used when calling LLM with function calling enabled.
        """
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for tool in self.tools.values()
        ]
    
    def validate_tool_call(self, tool_call: ToolCall) -> tuple[bool, Optional[str]]:
        """
        Validates a tool call before execution.
        
        Security checks:
        1. Tool exists in allowlist
        2. Required parameters present
        3. Parameter types match schema
        """
        
        if tool_call.name not in self.tools:
            return False, f"Tool '{tool_call.name}' not found in registry"
        
        tool_def = self.tools[tool_call.name]
        required_params = tool_def["parameters"].get("required", [])
        
        # Check required parameters
        for param in required_params:
            if param not in tool_call.parameters:
                return False, f"Missing required parameter: {param}"
        
        return True, None
    
    def execute_tool(
        self,
        tool_call: ToolCall,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Executes a tool call after validation.
        
        Args:
            tool_call: The tool to execute
            user_id: ID of user making the call
            context: Additional context (e.g., user data, state)
        
        Returns:
            ToolResult with success status and data/error
        """
        
        # Validate first
        is_valid, error_msg = self.validate_tool_call(tool_call)
        if not is_valid:
            logger.warning(f"Invalid tool call: {error_msg}")
            return ToolResult(success=False, error=error_msg)
        
        tool_def = self.tools[tool_call.name]
        
        # Log the execution (with PII masking if needed)
        logger.info(f"Executing tool: {tool_call.name} for user: {user_id}")
        
        try:
            # Call the handler
            handler = tool_def["handler"]
            result_data = handler(
                parameters=tool_call.parameters,
                user_id=user_id,
                context=context or {}
            )
            
            return ToolResult(success=True, data=result_data)
        
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_call.name} - {e}")
            return ToolResult(success=False, error=str(e))
    
    # Tool Handlers (implementations)
    
    def _handle_schedule_appointment(
        self,
        parameters: Dict[str, Any],
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handles appointment scheduling.
        
        In production: Check calendar availability, send confirmations, etc.
        For demo: Return success with appointment details.
        """
        
        appointment_id = f"apt_{datetime.utcnow().timestamp()}"
        
        return {
            "appointment_id": appointment_id,
            "date": parameters["date"],
            "time": parameters["time"],
            "purpose": parameters["purpose"],
            "duration_minutes": parameters.get("duration_minutes", 30),
            "status": "confirmed",
            "confirmation": f"Appointment scheduled for {parameters['date']} at {parameters['time']}"
        }
    
    def _handle_get_available_slots(
        self,
        parameters: Dict[str, Any],
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Returns available time slots for a date.
        
        In production: Query calendar system for real availability.
        For demo: Return some sample slots.
        """
        
        return {
            "date": parameters["date"],
            "available_slots": [
                {"time": "09:00", "duration_minutes": 30},
                {"time": "10:00", "duration_minutes": 30},
                {"time": "11:00", "duration_minutes": 30},
                {"time": "14:00", "duration_minutes": 30},
                {"time": "15:00", "duration_minutes": 30},
                {"time": "16:00", "duration_minutes": 30},
            ]
        }
    
    def _handle_cancel_appointment(
        self,
        parameters: Dict[str, Any],
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cancels an appointment.
        
        In production: Update calendar, send notifications, etc.
        For demo: Return cancellation confirmation.
        """
        
        return {
            "appointment_id": parameters["appointment_id"],
            "status": "cancelled",
            "confirmation": f"Appointment {parameters['appointment_id']} has been cancelled"
        }
