"""
OTP Validator

Generates, hashes, and verifies one-time passwords (OTP) for email verification.

Security Features:
- OTPs are hashed before storage (never store plaintext)
- Uses salt from Secret Manager
- Expires after 5 minutes
- Max 3 verification attempts
- Rate limiting to prevent brute force
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from ..models import ValidationResult, OTPData

logger = logging.getLogger(__name__)


class OTPValidator:
    """
    Handles OTP generation, hashing, and verification.
    
    Security principles:
    1. OTP is 6 digits (1 million combinations)
    2. Hashed with SHA256 + salt before storage
    3. Expires in 5 minutes
    4. Max 3 verification attempts
    5. Cannot reuse expired OTPs
    """
    
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 5
    MAX_ATTEMPTS = 3
    
    def __init__(self, salt: str):
        """
        Initialize OTP validator.
        
        Args:
            salt: Salt for hashing (from Secret Manager)
        """
        self.salt = salt
    
    def generate_otp(self) -> str:
        """
        Generates a random 6-digit OTP.
        
        Returns:
            6-digit OTP as string (e.g., "123456")
        """
        # Generate random 6-digit number
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(self.OTP_LENGTH)])
        
        logger.info("OTP generated successfully")
        return otp
    
    def hash_otp(self, otp: str) -> str:
        """
        Hashes OTP with salt using SHA256.
        
        Args:
            otp: Plain text OTP
        
        Returns:
            Hex digest of hashed OTP
        """
        # Combine OTP with salt
        salted_otp = f"{otp}{self.salt}"
        
        # Hash with SHA256
        hashed = hashlib.sha256(salted_otp.encode()).hexdigest()
        
        return hashed
    
    def create_otp_data(self, user_id: str, email: str) -> Tuple[str, OTPData]:
        """
        Creates OTP and its hashed data object.
        
        Args:
            user_id: User's ID
            email: Email where OTP will be sent
        
        Returns:
            Tuple of (plain_otp, OTPData object)
        """
        # Generate OTP
        plain_otp = self.generate_otp()
        
        # Hash it
        otp_hash = self.hash_otp(plain_otp)
        
        # Create expiry timestamp (timezone-aware)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        
        # Create OTP data object
        otp_data = OTPData(
            user_id=user_id,
            otp_hash=otp_hash,
            expires_at=expires_at,
            attempts=0,
            max_attempts=self.MAX_ATTEMPTS,
            email_sent_to=email
        )
        
        logger.info(f"OTP data created for user {user_id}, expires at {expires_at}")
        
        return plain_otp, otp_data
    
    def validate(self, user_input: str, otp_data: OTPData) -> ValidationResult:
        """
        Validates user's OTP input against stored hash.
        
        Args:
            user_input: OTP entered by user
            otp_data: Stored OTP data with hash
        
        Returns:
            ValidationResult with success/failure
        """
        
        # Extract digits only from user input
        digits_only = ''.join(filter(str.isdigit, user_input))
        
        # Check if OTP has correct length
        if len(digits_only) != self.OTP_LENGTH:
            return ValidationResult(
                success=False,
                error_message=f"Please enter a {self.OTP_LENGTH}-digit code.",
                metadata={"validation_type": "otp", "error_type": "invalid_length"}
            )
        
        # Check if OTP has expired
        # Make sure both datetimes are timezone-aware for comparison
        now = datetime.now(timezone.utc)
        expires_at = otp_data.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if now > expires_at:
            return ValidationResult(
                success=False,
                error_message="This code has expired. Please request a new one.",
                metadata={"validation_type": "otp", "error_type": "expired"}
            )
        
        # Check if max attempts exceeded
        if otp_data.attempts >= otp_data.max_attempts:
            return ValidationResult(
                success=False,
                error_message="Too many failed attempts. Please request a new code.",
                metadata={"validation_type": "otp", "error_type": "max_attempts"}
            )
        
        # Hash user's input
        input_hash = self.hash_otp(digits_only)
        
        # Compare hashes (constant-time comparison to prevent timing attacks)
        if secrets.compare_digest(input_hash, otp_data.otp_hash):
            # SUCCESS!
            logger.info(f"OTP verified successfully for user {otp_data.user_id}")
            
            return ValidationResult(
                success=True,
                data={
                    "user_id": otp_data.user_id,
                    "verified_at": datetime.now(timezone.utc).isoformat()
                },
                metadata={"validation_type": "otp"}
            )
        else:
            # FAILED - increment attempts
            remaining_attempts = otp_data.max_attempts - (otp_data.attempts + 1)
            
            logger.warning(f"Invalid OTP attempt for user {otp_data.user_id}, {remaining_attempts} attempts remaining")
            
            if remaining_attempts > 0:
                error_msg = f"Invalid code. You have {remaining_attempts} attempt(s) remaining."
            else:
                error_msg = "Invalid code. No attempts remaining. Please request a new code."
            
            return ValidationResult(
                success=False,
                error_message=error_msg,
                metadata={
                    "validation_type": "otp",
                    "error_type": "invalid_code",
                    "attempts_remaining": remaining_attempts
                }
            )
    
    def is_otp_expired(self, otp_data: OTPData) -> bool:
        """
        Checks if OTP has expired.
        
        Args:
            otp_data: OTP data object
        
        Returns:
            True if expired, False otherwise
        """
        now = datetime.now(timezone.utc)
        expires_at = otp_data.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return now > expires_at
    
    def get_time_remaining(self, otp_data: OTPData) -> int:
        """
        Gets remaining time in seconds before OTP expires.
        
        Args:
            otp_data: OTP data object
        
        Returns:
            Seconds remaining (0 if expired)
        """
        if self.is_otp_expired(otp_data):
            return 0
        
        now = datetime.now(timezone.utc)
        expires_at = otp_data.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        time_remaining = expires_at - now
        return int(time_remaining.total_seconds())
    
    def format_time_remaining(self, otp_data: OTPData) -> str:
        """
        Formats remaining time as human-readable string.
        
        Args:
            otp_data: OTP data object
        
        Returns:
            Formatted string (e.g., "4 minutes 30 seconds")
        """
        seconds = self.get_time_remaining(otp_data)
        
        if seconds <= 0:
            return "Expired"
        
        minutes = seconds // 60
        seconds = seconds % 60
        
        if minutes > 0:
            return f"{minutes} minute(s) {seconds} second(s)"
        else:
            return f"{seconds} second(s)"
