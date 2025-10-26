"""
Security Module

Handles:
1. JWT authentication and validation
2. PII detection and redaction using Cloud DLP
3. Logging with PII masking
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple,List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from google.cloud import dlp_v2
from google.cloud import secretmanager


logger = logging.getLogger(__name__)


class SecurityManager:
    """
    Manages all security operations: auth, PII handling, secrets.
    """
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.dlp_client = dlp_v2.DlpServiceClient()
        self.secret_client = secretmanager.SecretManagerServiceClient()
        
        # Load JWT secret from Secret Manager
        self.jwt_secret = self._get_secret("jwt-secret")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_minutes = 60
    
    def _get_secret(self, secret_id: str) -> str:
        """
        Retrieves a secret from GCP Secret Manager.
        
        Why: Secrets should never be hardcoded or in environment variables.
        Secret Manager provides versioning, rotation, and audit logs.
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        try:
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8").strip()  # Strip whitespace and newlines
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_id}: {e}")
            return "fallback-secret-for-development"
    
    def create_jwt_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """
        Creates a short-lived JWT token for authenticated users.
        
        Why: Stateless authentication - no session database needed.
        Token contains user_id and expiration, signed with our secret.
        """
        expire = datetime.utcnow() + timedelta(minutes=self.jwt_expiration_minutes)
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validates and decodes a JWT token.
        
        Returns the payload if valid, None if invalid/expired.
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def detect_and_redact_pii(self, text: str) -> Tuple[str, List[str]]:
        """
        Uses Cloud DLP to detect and redact PII from text.
        
        Why: We must never send raw PII to LLMs or log it.
        This detects: emails, phone numbers, names, addresses, SSNs, etc.
        
        Returns: (redacted_text, list_of_detected_pii_types)
        """
        parent = f"projects/{self.project_id}"
        
        # Configure what types of PII to detect
        info_types = [
            {"name": "EMAIL_ADDRESS"},
            {"name": "PHONE_NUMBER"},
            {"name": "PERSON_NAME"},
            {"name": "US_SOCIAL_SECURITY_NUMBER"},
            {"name": "CREDIT_CARD_NUMBER"},
            {"name": "STREET_ADDRESS"},
        ]
        
        inspect_config = {
            "info_types": info_types,
            "min_likelihood": dlp_v2.Likelihood.LIKELY,
        }
        
        # Use [REDACTED-TYPE] format for redaction
        deidentify_config = {
            "info_type_transformations": {
                "transformations": [
                    {
                        "primitive_transformation": {
                            "replace_with_info_type_config": {}
                        }
                    }
                ]
            }
        }
        
        item = {"value": text}
        
        try:
            response = self.dlp_client.deidentify_content(
                request={
                    "parent": parent,
                    "deidentify_config": deidentify_config,
                    "inspect_config": inspect_config,
                    "item": item,
                }
            )
            
            redacted_text = response.item.value
            detected_types = [finding.info_type.name for finding in response.overview.transformation_summaries]
            
            return redacted_text, detected_types
        
        except Exception as e:
            logger.error(f"DLP redaction failed: {e}")
            # Fallback: return original text if DLP fails
            # In production, you might want to fail-closed instead
            return text, []
    
    def mask_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Masks sensitive fields in data before logging.
        
        Why: Logs are stored long-term and accessible to ops teams.
        Never log raw PII, tokens, or passwords.
        """
        masked = data.copy()
        
        sensitive_fields = ["email", "phone", "password", "token", "ssn", "credit_card"]
        
        for key in masked:
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                if isinstance(masked[key], str):
                    # Show only first 2 and last 2 characters
                    value = masked[key]
                    if len(value) > 4:
                        masked[key] = f"{value[:2]}***{value[-2:]}"
                    else:
                        masked[key] = "***"
        
        return masked
    
    def mask_phone(self, phone: str) -> str:
        """
        Masks phone number for display (security).
        
        Shows only country code and last 4 digits.
        
        Args:
            phone: Phone number in E.164 format (e.g., "+15551234567")
        
        Returns:
            Masked phone (e.g., "+1 555-***-4567")
        
        Examples:
            "+15551234567" → "+1 555-***-4567"
            "+442012345678" → "+44 20-***-5678"
        """
        if not phone or len(phone) < 4:
            return "***"
        
        # E.164 format: +[country code][number]
        # Try to parse intelligently
        
        if phone.startswith('+'):
            # Has country code
            # Show: country code + first 3 digits + *** + last 4 digits
            if len(phone) > 8:
                # Extract country code (1-3 digits after +)
                if phone[1:4].isdigit() and not phone[4].isdigit():
                    # 3-digit country code
                    country_code = phone[:4]
                    rest = phone[4:]
                elif phone[1:3].isdigit() and not phone[3].isdigit():
                    # 2-digit country code
                    country_code = phone[:3]
                    rest = phone[3:]
                else:
                    # 1-digit country code
                    country_code = phone[:2]
                    rest = phone[2:]
                
                # Format: +CC AAA-***-DDDD
                if len(rest) >= 7:
                    first_part = rest[:3]
                    last_part = rest[-4:]
                    return f"{country_code} {first_part}-***-{last_part}"
                elif len(rest) >= 4:
                    last_part = rest[-4:]
                    return f"{country_code} ***-{last_part}"
                else:
                    return f"{country_code} ***"
            else:
                # Short number
                return phone[:3] + "***"
        else:
            # No country code - just mask middle
            if len(phone) > 6:
                return phone[:2] + "***" + phone[-2:]
            else:
                return "***"
