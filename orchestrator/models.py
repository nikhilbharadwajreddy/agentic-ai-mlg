"""
Data Models and Schemas

This file defines all data structures used throughout the application.
Uses Pydantic for validation and serialization.

KEY SECURITY FEATURES:
- PII detection models for DLP integration
- Audit logging for compliance
- Tool security levels (low/medium/high risk)
- Step-up authentication triggers
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# ============================================
# WORKFLOW STATES
# ============================================

class WorkflowStep(str, Enum):
    """
    Defines all possible steps in the user onboarding workflow.
    The state machine enforces this exact order - users CANNOT skip steps.
    
    Flow: AWAITING_TERMS → NAME → EMAIL → PHONE → OTP → VERIFIED → ACTIVE
    """
    AWAITING_TERMS = "awaiting_terms"
    AWAITING_NAME = "awaiting_name"
    AWAITING_EMAIL = "awaiting_email"
    AWAITING_PHONE = "awaiting_phone"
    AWAITING_OTP = "awaiting_otp"
    VERIFIED = "verified"
    ACTIVE = "active"
    SUSPENDED = "suspended"  # For security holds


# ============================================
# USER STATE & SESSION
# ============================================

class UserState(BaseModel):
    """
    Represents the current state of a user in the workflow.
    Stored in Firestore for each user session.
    
    SECURITY NOTE: 
    - 'data' field stores collected user info (name, email, phone)
    - OTP is stored HASHED, never plaintext
    - PII is redacted before sending to LLM
    """
    user_id: str
    current_step: WorkflowStep
    completed_steps: List[str] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # Security fields
    terms_agreed: bool = False
    terms_agreed_at: Optional[datetime] = None
    otp_hash: Optional[str] = None  # Hashed OTP, NEVER store plaintext
    otp_expires_at: Optional[datetime] = None
    failed_otp_attempts: int = 0
    max_otp_attempts: int = 3
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# ============================================
# APPOINTMENT SYSTEM MODELS
# ============================================

class Employee(BaseModel):
    """Sales rep/team member who takes appointments."""
    employee_id: str
    name: str
    role: str  # "Sales Rep", "Solutions Architect", etc.
    email: str
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TimeSlot(BaseModel):
    """Single time slot for booking."""
    slot_id: str
    employee_id: str
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM (24hr)
    end_time: str  # HH:MM
    is_booked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Appointment(BaseModel):
    """Booked appointment."""
    appointment_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    employee_id: str
    employee_name: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    purpose: str = "ML Solutions Demo"
    status: str = "confirmed"  # confirmed, cancelled, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


# ============================================
# API REQUEST/RESPONSE
# ============================================

class ChatRequest(BaseModel):
    """
    Incoming chat message from the frontend.
    
    SECURITY: 
    - user_id should come from authenticated JWT token, not user input
    - message will be scanned for PII before sending to LLM
    """
    user_id: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """
    Response sent back to the frontend.
    
    Includes current workflow state so frontend can show progress.
    """
    response: str
    current_step: str
    completed_steps: List[str]
    requires_action: Optional[str] = None  # e.g., "send_otp", "confirm_appointment"
    metadata: Optional[Dict[str, Any]] = None  # Additional context


# ============================================
# LLM INTERACTION
# ============================================

class LLMMessage(BaseModel):
    """
    Represents a message in the LLM conversation.
    Follows OpenAI/Vertex AI message format.
    """
    role: str  # "user", "assistant", or "system"
    content: str


class ExtractedIntent(BaseModel):
    """
    Structured data extracted by LLM from user message.
    Used for step validation.
    
    EXAMPLE: User says "Yes, I agree to terms"
    → LLM extracts: {intent_type: "agreement", confidence: 0.95, extracted_data: {agreed: true}}
    """
    intent_type: str
    confidence: float
    extracted_data: Dict[str, Any] = Field(default_factory=dict)


# ============================================
# TOOL CALLING
# ============================================

class ToolCall(BaseModel):
    """
    Represents a tool/function call from the LLM.
    
    SECURITY: Tool calls are validated against a registry.
    High-risk tools (e.g., payments) require step-up authentication.
    """
    name: str
    parameters: Dict[str, Any]
    reasoning: Optional[str] = None  # Why LLM chose this tool


class ToolSchema(BaseModel):
    """
    Definition of a callable tool - stored in tool registry.
    
    SECURITY LEVELS:
    - low: Read-only operations (get_balance, view_appointments)
    - medium: Modifications (create_appointment, update_profile)
    - high: Sensitive operations (transfer_money, delete_account)
    """
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema format
    requires_auth: bool = True
    requires_verification: bool = False  # Step-up MFA needed
    risk_level: Literal["low", "medium", "high"] = "low"
    allowed_steps: List[WorkflowStep] = Field(default_factory=list)  # Only callable in certain steps


class ToolResult(BaseModel):
    """
    Result from executing a tool.
    Returned to LLM and logged for audit trail.
    """
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: Optional[float] = None


# ============================================
# SECURITY & PII
# ============================================

class PIIDetectionResult(BaseModel):
    """
    Result from Cloud DLP scan.
    
    USAGE: Before sending user message to LLM, we:
    1. Scan for PII (names, emails, phone numbers, SSN, credit cards)
    2. Redact/tokenize PII
    3. Send redacted text to LLM
    4. Log that PII was detected
    """
    has_pii: bool
    pii_types: List[str] = Field(default_factory=list)  # e.g., ["EMAIL_ADDRESS", "PHONE_NUMBER"]
    redacted_text: str  # Text with PII replaced by [REDACTED]
    confidence: float = 0.0
    likelihood: Optional[str] = None  # "LIKELY", "VERY_LIKELY", etc.


class AuditLog(BaseModel):
    """
    Audit trail entry for compliance (SOC 2, GDPR, etc.)
    
    LOGGED EVENTS:
    - Workflow transitions (user moved from step X to Y)
    - Tool calls (user called appointment_schedule with params {...})
    - Auth attempts (user failed OTP 3 times)
    - PII detections (PII found in message)
    
    STORED IN: Cloud Logging + BigQuery for analysis
    """
    user_id: str
    event_type: str  # "workflow_transition", "tool_call", "auth_attempt", "pii_detected"
    event_data: Dict[str, Any]
    pii_detected: bool = False
    risk_score: float = 0.0  # 0.0 = safe, 1.0 = high risk
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# AUTHENTICATION
# ============================================

class AuthToken(BaseModel):
    """
    JWT token claims for authenticated users.
    
    SECURITY: 
    - Tokens are short-lived (10-15 minutes)
    - Refresh tokens stored securely
    - Contains minimal data (no PII)
    """
    user_id: str
    session_id: str
    issued_at: datetime
    expires_at: datetime
    scopes: List[str] = Field(default_factory=list)  # e.g., ["read:appointments", "write:profile"]


# ============================================
# RATE LIMITING
# ============================================

class RateLimitInfo(BaseModel):
    """
    Rate limit tracking per user.
    Prevents abuse and API flooding.
    """
    user_id: str
    endpoint: str
    requests_count: int
    window_start: datetime
    window_duration_seconds: int = 60  # 1 minute window
    limit: int = 100  # Max requests per window


# ============================================
# VALIDATION MODELS (NEW)
# ============================================

class ValidationResult(BaseModel):
    """
    Standard result format for all validators.
    
    USAGE:
    - success: True if validation passed
    - data: Extracted/validated data (e.g., {"first_name": "John", "last_name": "Smith"})
    - error_message: Human-readable error if validation failed
    - metadata: Additional info (e.g., confidence scores, suggestions)
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================
# USER MODELS (NEW)
# ============================================

class User(BaseModel):
    """
    User record stored in Firestore 'users' collection.
    
    INDEXED FIELDS:
    - email + last_name: For returning user detection
    
    SECURITY:
    - Phone stored with country code
    - All PII encrypted at rest by Firestore
    - verified flag indicates OTP verification completed
    """
    user_id: str
    email: str
    first_name: str
    last_name: str
    phone: str
    country_code: str  # e.g., "+1", "+44"
    verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


# ============================================
# OTP MODELS (NEW)
# ============================================

class OTPData(BaseModel):
    """
    OTP (One-Time Password) data for email verification.
    
    SECURITY:
    - OTP is HASHED before storage (never store plaintext)
    - Expires after 5 minutes
    - Max 3 verification attempts
    - Uses salt from Secret Manager
    """
    user_id: str
    otp_hash: str  # SHA256 hash of OTP + salt
    expires_at: datetime
    attempts: int = 0
    max_attempts: int = 3
    email_sent_to: str  # For audit trail
    created_at: datetime = Field(default_factory=datetime.utcnow)
