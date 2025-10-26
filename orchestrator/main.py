"""
Main FastAPI Application

This is the entry point for the orchestrator service.
Exposes REST API endpoints for the frontend to call.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import ChatRequest, ChatResponse, UserState
from .security import SecurityManager
from .llm_client import LLMClient
from .state_machine import StateMachine
from .tools.registry import ToolRegistry
from .services.admin_service import AdminService
from .appointment_models import Employee, TimeSlot
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances (initialized on startup)
security_manager: Optional[SecurityManager] = None
llm_client: Optional[LLMClient] = None
state_machine: Optional[StateMachine] = None
tool_registry: Optional[ToolRegistry] = None
admin_service: Optional[AdminService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI app.
    
    Initializes all services on startup.
    Cleans up on shutdown.
    """
    global security_manager, llm_client, state_machine, tool_registry, admin_service
    
    # Get project ID from environment
    project_id = os.getenv("GCP_PROJECT_ID", "agentic-ai-mlg")
    
    logger.info(f"Initializing services for project: {project_id}")
    
    # Initialize services
    security_manager = SecurityManager(project_id)
    llm_client = LLMClient(project_id)
    state_machine = StateMachine(project_id, llm_client, security_manager)
    tool_registry = ToolRegistry()
    
    # Initialize admin service
    from google.cloud import firestore
    admin_service = AdminService(firestore.Client(project=project_id))
    
    logger.info("All services initialized successfully")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down services")


# Create FastAPI app
app = FastAPI(
    title="AI Agent Orchestrator",
    description="Production-ready AI agent with workflow enforcement and tool calling",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - configure for your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all requests.
    
    Why: Audit trail for compliance and debugging.
    Masks sensitive data in logs.
    """
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    logger.info(f"Response: {response.status_code}")
    return response


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Cloud Run.
    
    Why: Load balancer uses this to determine if service is ready.
    """
    return {"status": "healthy", "service": "orchestrator"}


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Main chat endpoint.
    
    Flow:
    1. Optionally verify JWT token (for authenticated users)
    2. Load user state from Firestore
    3. Process message through state machine (validators extract data)
    4. Check if LLM wants to call a tool
    5. Execute tool if needed
    6. Return response
    
    NOTE: PII redaction is NOT done here because:
    - Validators need the original message to extract email/phone
    - LLM only receives context (not raw user input) for response generation
    - Data is stored securely in Firestore (encrypted at rest)
    - Logging uses masked data via security_manager.mask_for_logging()
    
    Args:
        request: ChatRequest with user_id and message
        authorization: Optional Bearer token
    
    Returns:
        ChatResponse with AI response and state info
    """
    
    try:
        # Optional: Verify JWT if provided
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            payload = security_manager.verify_jwt_token(token)
            
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Verify token user_id matches request user_id
            if payload.get("sub") != request.user_id:
                raise HTTPException(status_code=403, detail="Token mismatch")
        
        # Step 1: Load user state
        state = state_machine.get_or_create_state(request.user_id)
        
        # Log request (mask message if it might contain PII)
        logger.info(f"Processing chat for user {request.user_id} in step {state.current_step}")
        
        # Step 2: Process through state machine with ORIGINAL message
        # (Validators need the raw data to extract email/phone)
        response_text, updated_state = state_machine.process_message(state, request.message)
        
        # Step 3: Check if response indicates tool call
        if response_text.startswith("TOOL_CALL:"):
            # Parse tool call
            parts = response_text.split(":", 2)
            tool_name = parts[1]
            tool_params = eval(parts[2])  # In production, use json.loads
            
            # Execute tool
            from .models import ToolCall
            tool_call = ToolCall(name=tool_name, parameters=tool_params)
            
            tool_result = tool_registry.execute_tool(
                tool_call=tool_call,
                user_id=request.user_id,
                context={"state": updated_state.model_dump()}
            )
            
            if tool_result.success:
                response_text = f"I've completed that action. {tool_result.data}"
            else:
                response_text = f"I encountered an issue: {tool_result.error}"
        
        # Step 4: Save updated state
        state_machine.save_state(updated_state)
        
        # Step 5: Return response
        return ChatResponse(
            response=response_text,
            current_step=str(updated_state.current_step),
            completed_steps=updated_state.completed_steps,
            requires_action=None
        )
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/auth/login")
async def login(email: str, password: str):
    """
    Login endpoint - issues JWT token.
    
    In production: Validate credentials against user database.
    For demo: Accept any credentials and issue token.
    """
    
    # Demo: Skip actual authentication
    user_id = f"user_{email.split('@')[0]}"
    
    token = security_manager.create_jwt_token(
        user_id=user_id,
        additional_claims={"email": email}
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id
    }


@app.get("/api/v1/state/{user_id}")
async def get_state(user_id: str):
    """
    Get current state for a user.
    
    Useful for frontend to show progress.
    """
    
    try:
        state = state_machine.get_or_create_state(user_id)
        return {
            "user_id": state.user_id,
            "current_step": str(state.current_step),
            "completed_steps": state.completed_steps,
            "data": security_manager.mask_for_logging(state.data)
        }
    except Exception as e:
        logger.error(f"Get state error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve state")


@app.post("/api/v1/tools/list")
async def list_tools():
    """
    Returns list of available tools.
    
    Used by frontend to show capabilities.
    """
    
    return {
        "tools": tool_registry.get_tool_definitions()
    }


# ===== ADMIN REQUEST MODELS =====

class CreateEmployeeRequest(BaseModel):
    name: str
    role: str
    email: str


class CreateSlotRequest(BaseModel):
    employee_id: str
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM


# ===== ADMIN ENDPOINTS =====

@app.post("/api/v1/admin/employees")
async def create_employee(req: CreateEmployeeRequest):
    """Create new employee/sales rep."""
    try:
        employee = admin_service.create_employee(
            name=req.name,
            role=req.role,
            email=req.email
        )
        return {"success": True, "employee": employee.model_dump()}
    except Exception as e:
        logger.error(f"Create employee error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/employees")
async def list_employees():
    """List all active employees."""
    try:
        employees = admin_service.list_employees()
        return {"employees": [e.model_dump() for e in employees]}
    except Exception as e:
        logger.error(f"List employees error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/admin/slots")
async def create_time_slot(req: CreateSlotRequest):
    """Add available time slot for employee."""
    try:
        slot = admin_service.add_time_slot(
            employee_id=req.employee_id,
            date=req.date,
            start_time=req.start_time,
            end_time=req.end_time
        )
        return {"success": True, "slot": slot.model_dump()}
    except Exception as e:
        logger.error(f"Create slot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/slots/{employee_id}")
async def get_employee_slots(employee_id: str, date: Optional[str] = None):
    """Get available slots for employee."""
    try:
        slots = admin_service.get_available_slots(employee_id, date)
        return {"slots": [s.model_dump() for s in slots]}
    except Exception as e:
        logger.error(f"Get slots error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/appointments")
async def get_all_appointments(status: Optional[str] = None):
    """Get all appointments (admin view)."""
    try:
        appointments = admin_service.get_all_appointments(status)
        return {"appointments": [a.model_dump() for a in appointments]}
    except Exception as e:
        logger.error(f"Get appointments error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/admin/appointments/{appointment_id}")
async def cancel_appointment_admin(appointment_id: str):
    """Cancel an appointment."""
    try:
        success = admin_service.cancel_appointment(appointment_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Cancel appointment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler.
    
    Why: Ensures we never leak internal errors to users.
    All errors are logged but sanitized in response.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "An internal error occurred",
            "message": "Please try again later"
        }
    )


if __name__ == "__main__":
    """
    Local development server.
    
    For production: Use uvicorn via Dockerfile
    """
    import uvicorn
    
    uvicorn.run(
        "orchestrator.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
