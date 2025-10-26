"""
Name Validator

Uses LLM to intelligently parse and validate names from natural language input.

Why LLM for names:
- Handles various formats: "John Smith", "I'm John Smith", "Call me John"
- Detects if only first name vs full name provided
- Handles cultural variations: "O'Brien", "Jean-Luc", "María García"
- Understands context and natural language
"""

import logging
from typing import TYPE_CHECKING

from ..models import ValidationResult, LLMMessage

if TYPE_CHECKING:
    from ..llm_client import LLMClient

logger = logging.getLogger(__name__)


class NameValidator:
    """
    Validates names using LLM for intelligent parsing.
    
    Key features:
    - Detects first name only vs first + last name
    - Handles natural language: "My name is...", "Call me...", "I'm..."
    - Handles special characters and cultural names
    - Provides helpful feedback if incomplete
    """
    
    def __init__(self):
        """
        Initialize name validator.
        
        Note: LLM client is passed to validate() method, not stored,
        to avoid circular imports.
        """
        pass
    
    def validate(self, user_input: str, llm_client: 'LLMClient') -> ValidationResult:
        """
        Validates name input using LLM for intelligent parsing.
        
        Args:
            user_input: User's message that should contain their name
            llm_client: LLM client for parsing
        
        Returns:
            ValidationResult with:
            - success: True if full name (first + last) detected
            - data: {"first_name": str, "last_name": str}
            - error_message: Helpful message if incomplete
        """
        
        # Clean input
        user_input = user_input.strip()
        
        if not user_input:
            return ValidationResult(
                success=False,
                error_message="I didn't catch your name. Could you please tell me your full name?"
            )
        
        # Use LLM to extract name components
        schema = {
            "has_first_name": {
                "type": "boolean",
                "description": "True if first name is present"
            },
            "has_last_name": {
                "type": "boolean",
                "description": "True if last name is present"
            },
            "first_name": {
                "type": "string",
                "description": "The person's first name (if detected)"
            },
            "last_name": {
                "type": "string",
                "description": "The person's last name (if detected)"
            },
            "full_name": {
                "type": "string",
                "description": "The complete name as extracted"
            }
        }
        
        messages = [
            LLMMessage(
                role="system",
                content="""You are a name parser. Extract the person's first and last name from their message.
                
Rules:
- Detect if they provided only first name or full name (first + last)
- Handle natural language: "My name is X", "I'm X", "Call me X"
- Handle cultural names with special characters: O'Brien, Jean-Luc, María, etc.
- If only first name detected, set has_last_name to false
- If both names detected, set both to true

Examples:
- "John" → has_first_name=true, has_last_name=false, first_name="John"
- "John Smith" → has_first_name=true, has_last_name=true, first_name="John", last_name="Smith"
- "My name is Sarah Johnson" → has_first_name=true, has_last_name=true, first_name="Sarah", last_name="Johnson"
- "I'm Mike" → has_first_name=true, has_last_name=false, first_name="Mike"
- "Call me Dr. James O'Brien" → has_first_name=true, has_last_name=true, first_name="James", last_name="O'Brien"
"""
            ),
            LLMMessage(
                role="user",
                content=user_input
            )
        ]
        
        try:
            # Extract name data using LLM
            extracted = llm_client.extract_structured_data(messages, schema)
            
            has_first = extracted.get("has_first_name", False)
            has_last = extracted.get("has_last_name", False)
            first_name = extracted.get("first_name", "").strip()
            last_name = extracted.get("last_name", "").strip()
            
            # Validate extraction
            if not has_first or not first_name:
                return ValidationResult(
                    success=False,
                    error_message="I couldn't detect your name in that message. Could you please provide your full name (first and last)?"
                )
            
            if not has_last or not last_name:
                # Only first name detected - ask for full name
                return ValidationResult(
                    success=False,
                    error_message=f"Thanks, {first_name}! Could you also provide your last name? I need your full name to continue.",
                    data={"first_name": first_name},  # Save partial data
                    metadata={
                        "validation_type": "name",
                        "incomplete": True,
                        "missing": "last_name"
                    }
                )
            
            # Both names present - SUCCESS!
            logger.info(f"Name validated successfully: {first_name} {last_name}")
            
            return ValidationResult(
                success=True,
                data={
                    "first_name": first_name,
                    "last_name": last_name,
                    "full_name": f"{first_name} {last_name}"
                },
                metadata={
                    "validation_type": "name",
                    "complete": True
                }
            )
        
        except Exception as e:
            logger.error(f"Name validation error: {e}")
            return ValidationResult(
                success=False,
                error_message="I'm having trouble processing that. Could you please provide your full name (first and last)?"
            )
    
    def is_valid_name_format(self, name: str) -> bool:
        """
        Basic validation of name format (non-LLM fallback).
        
        Args:
            name: Name string to validate
        
        Returns:
            True if valid format, False otherwise
        """
        if not name or not name.strip():
            return False
        
        # Basic checks
        name = name.strip()
        
        # Too short
        if len(name) < 2:
            return False
        
        # Too long (probably not a real name)
        if len(name) > 100:
            return False
        
        # Should contain at least some letters
        if not any(c.isalpha() for c in name):
            return False
        
        # Should not be all numbers
        if name.replace(' ', '').isdigit():
            return False
        
        return True
    
    def has_multiple_parts(self, name: str) -> bool:
        """
        Checks if name has multiple parts (likely full name).
        
        Args:
            name: Name string
        
        Returns:
            True if multiple parts detected
        """
        parts = name.strip().split()
        
        # Filter out very short parts (initials, titles)
        significant_parts = [p for p in parts if len(p) > 1]
        
        return len(significant_parts) >= 2
