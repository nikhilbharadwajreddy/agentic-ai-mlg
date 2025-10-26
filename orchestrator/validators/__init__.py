"""
Validators Module

Contains all validation logic for user inputs.
Each validator returns a ValidationResult with success/failure and extracted data.

Validators:
- name_validator: Uses LLM to parse and validate full names
- email_validator: Regex validation + DB lookup for returning users
- phone_validator: International phone number validation
- otp_validator: OTP generation and verification
"""

from .name_validator import NameValidator
from .email_validator import EmailValidator
from .phone_validator import PhoneValidator
from .otp_validator import OTPValidator

__all__ = [
    "NameValidator",
    "EmailValidator",
    "PhoneValidator",
    "OTPValidator",
]
