"""
State Machine Module - NEW ARCHITECTURE

Enforces strict workflow transitions with CODE-BASED validation and LLM-GENERATED responses.

KEY PRINCIPLE:
- CODE validates data (deterministic, reliable)
- LLM generates responses (natural, conversational)
- EXCEPTION: Name validation uses LLM (complex parsing)

Flow: Terms → Name → Email → Phone → OTP → Active
"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from google.cloud import firestore

from .models import WorkflowStep, UserState, User, OTPData
from .llm_client import LLMClient
from .validators import NameValidator, EmailValidator, PhoneValidator, OTPValidator
from .services import EmailService, UserService
from .vertex_agent_client import VertexAgent

logger = logging.getLogger(__name__)


class StateMachine:
    """
    Manages user workflow state with strict validation and natural responses.
    
    NEW ARCHITECTURE:
    1. User sends message
    2. State machine validates using CODE (except name which uses LLM)
    3. If validation succeeds → LLM generates natural response
    4. State transitions
    5. Response sent to user
    """
    
    # Define valid state transitions
    TRANSITIONS = {
        WorkflowStep.AWAITING_TERMS: [WorkflowStep.AWAITING_NAME],
        WorkflowStep.AWAITING_NAME: [WorkflowStep.AWAITING_EMAIL],
        WorkflowStep.AWAITING_EMAIL: [WorkflowStep.AWAITING_PHONE],
        WorkflowStep.AWAITING_PHONE: [WorkflowStep.AWAITING_OTP],
        WorkflowStep.AWAITING_OTP: [WorkflowStep.ACTIVE],
        WorkflowStep.ACTIVE: [WorkflowStep.ACTIVE],  # Stay active
    }
    
    def __init__(
        self,
        project_id: str,
        llm_client: LLMClient,
        security_manager=None
    ):
        """
        Initialize state machine with all dependencies.
        
        Args:
            project_id: GCP project ID
            llm_client: LLM client for response generation
            security_manager: Security manager for phone masking
        """
        self.project_id = project_id
        self.llm_client = llm_client
        self.security_manager = security_manager
        self.db = firestore.Client(project=project_id)
        
        # Initialize validators
        self.name_validator = NameValidator()
        self.email_validator = EmailValidator(self.db)
        self.phone_validator = PhoneValidator()
        
        # Initialize OTP validator (get salt from Secret Manager)
        otp_salt = self._get_otp_salt()
        self.otp_validator = OTPValidator(otp_salt)
        
        # Initialize services
        email_api_key = self._get_email_api_key()
        from_email = self._get_from_email()
        self.email_service = EmailService(email_api_key, from_email)
        self.user_service = UserService(self.db)
        
        # Initialize Vertex AI Agent for ACTIVE conversations
        self.vertex_agent = VertexAgent(project_id)
        
        logger.info("State machine initialized with new architecture")
    
    def _get_otp_salt(self) -> str:
        """Gets OTP salt from Secret Manager"""
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/otp-salt/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8").strip()  # Strip whitespace
        except Exception as e:
            logger.warning(f"Failed to get OTP salt: {e}, using fallback")
            return "fallback-salt-for-development"
    
    def _get_email_api_key(self) -> str:
        """Gets SendGrid API key from Secret Manager"""
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/email-api-key/versions/latest"
            response = client.access_secret_version(request={"name": name})
            api_key = response.payload.data.decode("UTF-8").strip()  # Strip whitespace and newlines
            return api_key
        except Exception as e:
            logger.warning(f"Failed to get email API key: {e}, using placeholder")
            return "PLACEHOLDER_SENDGRID_API_KEY"
    
    def _get_from_email(self) -> str:
        """Gets sender email address from Secret Manager or environment variable"""
        import os
        
        # Try environment variable first
        from_email = os.getenv("FROM_EMAIL")
        if from_email:
            from_email = from_email.strip()  # Strip whitespace
            logger.info(f"Using FROM_EMAIL from environment: {from_email}")
            return from_email
        
        # Try Secret Manager
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/from-email/versions/latest"
            response = client.access_secret_version(request={"name": name})
            from_email = response.payload.data.decode("UTF-8").strip()  # Strip whitespace
            logger.info(f"Using from-email from Secret Manager: {from_email}")
            return from_email
        except Exception as e:
            logger.warning(f"Failed to get from-email from Secret Manager: {e}")
        
        # Fallback to default
        default_email = "ceo@mlground.com"
        logger.warning(f"Using fallback from_email: {default_email}")
        return default_email
    
    def get_or_create_state(self, user_id: str) -> UserState:
        """
        Retrieves user state from Firestore or creates new state.
        """
        doc_ref = self.db.collection("user_states").document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            return UserState(**data)
        else:
            # New user - start at beginning
            new_state = UserState(
                user_id=user_id,
                current_step=WorkflowStep.AWAITING_TERMS,
                completed_steps=[],
                data={}
            )
            doc_ref.set(new_state.model_dump())
            return new_state
    
    def save_state(self, state: UserState):
        """
        Persists user state to Firestore.
        """
        state.updated_at = datetime.now(timezone.utc)
        doc_ref = self.db.collection("user_states").document(state.user_id)
        doc_ref.set(state.model_dump())
        logger.info(f"State saved for user {state.user_id}: {state.current_step}")
    
    def process_message(
        self,
        state: UserState,
        message: str
    ) -> Tuple[str, UserState]:
        """
        Main processing logic - routes to appropriate handler based on current step.
        
        Returns: (response_text, updated_state)
        """
        
        if state.current_step == WorkflowStep.AWAITING_TERMS:
            return self._handle_terms(state, message)
        
        elif state.current_step == WorkflowStep.AWAITING_NAME:
            return self._handle_name(state, message)
        
        elif state.current_step == WorkflowStep.AWAITING_EMAIL:
            return self._handle_email(state, message)
        
        elif state.current_step == WorkflowStep.AWAITING_PHONE:
            return self._handle_phone(state, message)
        
        elif state.current_step == WorkflowStep.AWAITING_OTP:
            return self._handle_otp(state, message)
        
        elif state.current_step == WorkflowStep.ACTIVE:
            return self._handle_active_conversation(state, message)
        
        else:
            response = self.llm_client.generate_response({"step": "unknown"})
            return response, state
    
    def _handle_terms(self, state: UserState, message: str) -> Tuple[str, UserState]:
        """
        Step 1: Terms and Conditions acceptance.
        
        NEW FLOW:
        1. Check if message is "TERMS_ACCEPTED" (from button)
        2. Transition state
        3. LLM generates welcoming response
        """
        
        # Simple check for terms acceptance
        if message == "TERMS_ACCEPTED" or "accept" in message.lower() or "agree" in message.lower():
            # SUCCESS - terms accepted
            state.completed_steps.append("terms_agreed")
            state.data["terms_agreed_at"] = datetime.now(timezone.utc).isoformat()
            state.terms_agreed = True
            state.terms_agreed_at = datetime.now(timezone.utc)
            state.current_step = WorkflowStep.AWAITING_NAME
            
            # LLM generates natural welcome response
            response = self.llm_client.generate_response({
                "step": "terms_accepted"
            })
            
            return response, state
        else:
            # Not yet accepted
            response = self.llm_client.generate_response({
                "step": "awaiting_terms",
                "error": "User has not explicitly accepted terms"
            })
            return response, state
    
    def _handle_name(self, state: UserState, message: str) -> Tuple[str, UserState]:
        """
        Step 2: Name collection.
        
        NEW FLOW:
        1. LLM validates name (detects first + last)
        2. If valid → Store data, transition state, LLM generates response
        3. If invalid → LLM generates helpful error message
        """
        
        # Use LLM to validate name
        result = self.name_validator.validate(message, self.llm_client)
        
        if result.success:
            # SUCCESS - full name extracted
            state.data["first_name"] = result.data["first_name"]
            state.data["last_name"] = result.data["last_name"]
            state.completed_steps.append("name_collected")
            state.current_step = WorkflowStep.AWAITING_EMAIL
            
            # LLM generates natural response
            response = self.llm_client.generate_response({
                "step": "name_collected",
                "first_name": result.data["first_name"],
                "last_name": result.data["last_name"]
            })
            
            return response, state
        else:
            # FAILED - incomplete name
            # LLM generates helpful prompt
            response = self.llm_client.generate_response({
                "step": "name_incomplete",
                "error": result.error_message,
                "first_name": result.data.get("first_name") if result.data else None
            })
            
            return response, state
    
    def _handle_email(self, state: UserState, message: str) -> Tuple[str, UserState]:
        """
        Step 3: Email collection.
        
        NEW FLOW:
        1. Extract email from message text
        2. CODE validates email format
        3. CODE checks DB for returning user (email + last_name)
        4. If returning user → LLM generates welcome back message with masked phone
        5. If new user → LLM generates normal transition
        """
        
        # Extract last name from state
        last_name = state.data.get("last_name")
        
        # First, try to extract email from the message
        # This handles cases like "my email is user@example.com" or just "user@example.com"
        extracted_email = self.email_validator.extract_email_from_text(message)
        
        # If no email found in text, try the message as-is (cleaned)
        email_to_validate = extracted_email if extracted_email else message.strip()
        
        # CODE validates email
        result = self.email_validator.validate(email_to_validate, last_name)
        
        if result.success:
            email = result.data["email"]
            is_returning = result.data["is_returning_user"]
            user_data = result.data.get("user_data")
            
            # Store email
            state.data["email"] = email
            state.completed_steps.append("email_collected")
            
            if is_returning and user_data:
                # RETURNING USER
                state.data["returning_user"] = True
                state.data["existing_phone"] = user_data.get("phone")
                state.data["existing_country_code"] = user_data.get("country_code")
                
                # Mask phone for display
                phone_masked = "***"
                if self.security_manager and user_data.get("phone"):
                    phone_masked = self.security_manager.mask_phone(user_data["phone"])
                elif self.phone_validator and user_data.get("phone"):
                    phone_masked = self.phone_validator.mask_phone_number(user_data["phone"])
                
                # Transition to phone step
                state.current_step = WorkflowStep.AWAITING_PHONE
                
                # LLM generates welcome back message
                response = self.llm_client.generate_response({
                    "step": "email_returning_user",
                    "first_name": state.data.get("first_name"),
                    "email": email,
                    "is_returning_user": True,
                    "phone_masked": phone_masked
                })
                
                # Backend injects masked phone into response
                if phone_masked not in response:
                    response += f" ({phone_masked})"
                
                return response, state
            else:
                # NEW USER
                state.data["returning_user"] = False
                state.current_step = WorkflowStep.AWAITING_PHONE
                
                # LLM generates normal transition
                response = self.llm_client.generate_response({
                    "step": "email_collected",
                    "email": email
                })
                
                return response, state
        else:
            # FAILED - invalid email
            response = self.llm_client.generate_response({
                "step": "email_invalid",
                "error": result.error_message
            })
            
            return response, state
    
    def _handle_phone(self, state: UserState, message: str) -> Tuple[str, UserState]:
        """
        Step 4: Phone collection.
        
        NEW FLOW:
        1. Extract phone from message text
        2. CODE validates phone format and country code
        3. Store phone
        4. Generate OTP
        5. Send email with OTP
        6. LLM generates confirmation message
        """
        
        # First, try to extract phone from the message
        # This handles cases like "my phone is +1 555-123-4567" or just "+1 555-123-4567"
        extracted_phone = self.phone_validator.extract_phone_from_text(message)
        
        # If no phone found in text, try the message as-is
        phone_to_validate = extracted_phone if extracted_phone else message
        
        # CODE validates phone
        result = self.phone_validator.validate(phone_to_validate)
        
        if result.success:
            # SUCCESS - valid phone
            phone = result.data["phone"]  # E.164 format
            country_code = result.data["country_code"]
            
            # Store phone
            state.data["phone"] = phone
            state.data["country_code"] = country_code
            state.completed_steps.append("phone_collected")
            
            # Generate OTP
            plain_otp, otp_data = self.otp_validator.create_otp_data(
                user_id=state.user_id,
                email=state.data["email"]
            )
            
            # Store OTP hash in state
            state.otp_hash = otp_data.otp_hash
            state.otp_expires_at = otp_data.expires_at
            state.failed_otp_attempts = 0
            
            # Send OTP email
            email_sent = self.email_service.send_otp_email(
                to_email=state.data["email"],
                otp_code=plain_otp,
                first_name=state.data.get("first_name"),
                expiry_minutes=5
            )
            
            if email_sent:
                # Transition to OTP step
                state.current_step = WorkflowStep.AWAITING_OTP
                
                # LLM generates confirmation
                response = self.llm_client.generate_response({
                    "step": "otp_sent",
                    "email": state.data["email"]
                })
                
                return response, state
            else:
                # Email failed to send
                response = self.llm_client.generate_response({
                    "step": "otp_send_failed",
                    "error": "Failed to send verification email"
                })
                return response, state
        else:
            # FAILED - invalid phone
            response = self.llm_client.generate_response({
                "step": "phone_invalid",
                "error": result.error_message
            })
            
            return response, state
    
    def _handle_otp(self, state: UserState, message: str) -> Tuple[str, UserState]:
        """
        Step 5: OTP verification.
        
        NEW FLOW:
        1. CODE validates OTP (hash comparison)
        2. If valid → Create/update user in DB, mark verified, LLM celebrates
        3. If invalid → Increment attempts, LLM encourages retry
        """
        
        # Reconstruct OTP data from state
        otp_data = OTPData(
            user_id=state.user_id,
            otp_hash=state.otp_hash,
            expires_at=state.otp_expires_at,
            attempts=state.failed_otp_attempts,
            email_sent_to=state.data["email"]
        )
        
        # CODE validates OTP
        result = self.otp_validator.validate(message, otp_data)
        
        if result.success:
            # SUCCESS - OTP verified!
            state.completed_steps.append("otp_verified")
            
            # Create or update user in database
            user = User(
                user_id=state.user_id,
                email=state.data["email"],
                first_name=state.data["first_name"],
                last_name=state.data["last_name"],
                phone=state.data["phone"],
                country_code=state.data["country_code"],
                verified=True,
                last_login=datetime.now(timezone.utc)
            )
            
            self.user_service.create_user(user)
            
            # Transition to ACTIVE
            state.current_step = WorkflowStep.ACTIVE
            
            # LLM generates success message
            response = self.llm_client.generate_response({
                "step": "otp_verified",
                "first_name": state.data["first_name"]
            })
            
            return response, state
        else:
            # FAILED - invalid OTP
            # Increment attempts
            state.failed_otp_attempts = otp_data.attempts + 1
            
            # LLM generates retry message
            response = self.llm_client.generate_response({
                "step": "otp_invalid",
                "error": result.error_message,
                "attempts_remaining": result.metadata.get("attempts_remaining", 0) if result.metadata else 0
            })
            
            return response, state
    
    def _handle_active_conversation(self, state: UserState, message: str) -> Tuple[str, UserState]:
        """
        Step 6: Active conversation with Vertex AI Agent.
        
        Hand off to Vertex AI Agent for booking appointments and company info.
        """
        
        # Build context for agent
        context = {
            "customer_id": state.user_id,
            "customer_name": f"{state.data.get('first_name', '')} {state.data.get('last_name', '')}".strip(),
            "customer_email": state.data.get('email', '')
        }
        
        # Call Vertex AI Agent (handle async)
        import asyncio
        try:
            response = asyncio.run(self.vertex_agent.send_message(
                user_id=state.user_id,
                message=message,
                context=context
            ))
        except Exception as e:
            logger.error(f"Agent call failed: {e}")
            response = "I'm having trouble connecting. Please try again."
        
        return response, state
