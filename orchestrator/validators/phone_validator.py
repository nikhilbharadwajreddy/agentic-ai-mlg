"""
Phone Validator

Validates international phone numbers using Google's libphonenumber.

Features:
- Validates phone format with country code
- Parses international numbers correctly
- Extracts country code and national number
- Handles various input formats
"""

import logging
import phonenumbers
from phonenumbers import NumberParseException
from typing import Optional

from ..models import ValidationResult

logger = logging.getLogger(__name__)


class PhoneValidator:
    """
    Validates phone numbers using Google's libphonenumber library.
    
    Accepts formats like:
    - +1 555-123-4567
    - +44 20 1234 5678
    - 00 1 555 123 4567
    - (555) 123-4567 (if region specified)
    """
    
    def __init__(self, default_region: str = "US"):
        """
        Initialize validator.
        
        Args:
            default_region: Default country code if not specified (ISO 3166-1 alpha-2)
        """
        self.default_region = default_region
    
    def validate(self, phone_input: str, region: Optional[str] = None) -> ValidationResult:
        """
        Validates phone number and extracts components.
        
        Args:
            phone_input: Phone number string (any format)
            region: Optional region code (e.g., "US", "GB")
        
        Returns:
            ValidationResult with:
            - success: True if valid
            - data: {
                "phone": full international format (+15551234567),
                "country_code": country calling code (+1),
                "national_number": national format (5551234567),
                "formatted": human-readable format (+1 555-123-4567)
              }
            - error_message: Error if validation failed
        """
        
        # Clean input
        phone_input = phone_input.strip()
        
        if not phone_input:
            return ValidationResult(
                success=False,
                error_message="Please provide a phone number."
            )
        
        # Use provided region or default
        parse_region = region or self.default_region
        
        try:
            # Parse phone number
            parsed = phonenumbers.parse(phone_input, parse_region)
            
            # Validate if it's a valid number
            if not phonenumbers.is_valid_number(parsed):
                return ValidationResult(
                    success=False,
                    error_message="That doesn't appear to be a valid phone number. Please include your country code (e.g., +1 for US)."
                )
            
            # Extract components
            country_code = f"+{parsed.country_code}"
            national_number = str(parsed.national_number)
            full_number = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
            formatted = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            
            # Get region code
            region_code = phonenumbers.region_code_for_number(parsed)
            
            return ValidationResult(
                success=True,
                data={
                    "phone": full_number,  # E.164 format: +15551234567
                    "country_code": country_code,
                    "national_number": national_number,
                    "formatted": formatted,  # Human readable: +1 555-123-4567
                    "region": region_code
                },
                metadata={
                    "validation_type": "phone",
                    "number_type": self._get_number_type(parsed)
                }
            )
        
        except NumberParseException as e:
            # Handle parsing errors
            error_messages = {
                NumberParseException.INVALID_COUNTRY_CODE: 
                    "Invalid country code. Please include a valid country code (e.g., +1 for US, +44 for UK).",
                NumberParseException.NOT_A_NUMBER:
                    "That doesn't look like a phone number. Please check and try again.",
                NumberParseException.TOO_SHORT_NSN:
                    "That phone number seems too short. Please provide the complete number.",
                NumberParseException.TOO_LONG:
                    "That phone number seems too long. Please check and try again.",
            }
            
            error_msg = error_messages.get(
                e.error_type,
                "Unable to validate phone number. Please provide a valid number with country code."
            )
            
            logger.warning(f"Phone validation failed: {e}")
            
            return ValidationResult(
                success=False,
                error_message=error_msg
            )
        
        except Exception as e:
            logger.error(f"Unexpected error in phone validation: {e}")
            return ValidationResult(
                success=False,
                error_message="Unable to process phone number. Please try again."
            )
    
    def _get_number_type(self, parsed_number) -> str:
        """
        Gets the type of phone number (mobile, fixed line, etc.)
        
        Args:
            parsed_number: Parsed PhoneNumber object
        
        Returns:
            Type as string
        """
        number_type = phonenumbers.number_type(parsed_number)
        
        type_mapping = {
            phonenumbers.PhoneNumberType.MOBILE: "mobile",
            phonenumbers.PhoneNumberType.FIXED_LINE: "fixed_line",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
            phonenumbers.PhoneNumberType.TOLL_FREE: "toll_free",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "premium_rate",
            phonenumbers.PhoneNumberType.VOIP: "voip",
            phonenumbers.PhoneNumberType.UNKNOWN: "unknown"
        }
        
        return type_mapping.get(number_type, "unknown")
    
    def extract_phone_from_text(self, text: str, region: Optional[str] = None) -> Optional[str]:
        """
        Attempts to extract a phone number from natural language text.
        
        Examples:
        - "my number is +1 555-123-4567" → "+15551234567"
        - "call me at 555 123 4567" → "+15551234567" (if region=US)
        
        Args:
            text: Text that may contain a phone number
            region: Optional region for context
        
        Returns:
            Extracted phone in E.164 format if found, None otherwise
        """
        parse_region = region or self.default_region
        
        try:
            # Try to find phone numbers in text
            matches = phonenumbers.PhoneNumberMatcher(text, parse_region)
            
            for match in matches:
                if phonenumbers.is_valid_number(match.number):
                    return phonenumbers.format_number(
                        match.number,
                        phonenumbers.PhoneNumberFormat.E164
                    )
            
            return None
        
        except Exception as e:
            logger.error(f"Error extracting phone from text: {e}")
            return None
    
    def mask_phone_number(self, phone: str) -> str:
        """
        Masks phone number for display (security).
        
        Examples:
        - "+15551234567" → "+1 555-***-4567"
        - "+442012345678" → "+44 20 ****5678"
        
        Args:
            phone: Phone number in E.164 format
        
        Returns:
            Masked phone number
        """
        try:
            parsed = phonenumbers.parse(phone, None)
            formatted = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            
            # Mask middle digits
            # Split by spaces/hyphens
            parts = formatted.split()
            
            if len(parts) >= 3:
                # Mask middle part(s)
                for i in range(1, len(parts) - 1):
                    parts[i] = '***'
                return ' '.join(parts)
            elif len(parts) == 2:
                # Mask part of the number
                number_part = parts[1]
                if len(number_part) > 4:
                    masked = '***' + number_part[-4:]
                    return f"{parts[0]} {masked}"
            
            # Fallback: mask middle characters
            if len(formatted) > 8:
                visible_start = 6
                visible_end = 4
                masked = formatted[:visible_start] + '***' + formatted[-visible_end:]
                return masked
            
            return formatted
        
        except Exception as e:
            logger.error(f"Error masking phone: {e}")
            # Fallback: simple masking
            if len(phone) > 6:
                return phone[:3] + '***' + phone[-2:]
            return '***'
