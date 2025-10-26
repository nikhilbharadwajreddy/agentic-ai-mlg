"""
Email Validator

Validates email format and checks for returning users in database.

Features:
- Regex validation for email format
- Database lookup for email + last_name match
- Returns whether user is returning or new
"""

import re
import logging
from typing import Optional
from google.cloud import firestore

from ..models import ValidationResult

logger = logging.getLogger(__name__)


class EmailValidator:
    """
    Validates email addresses and checks for returning users.
    
    Validation rules:
    1. Must contain @ symbol
    2. Must contain domain with .
    3. Basic RFC 5322 compliance
    4. Check if email + last_name exists in DB
    """
    
    # RFC 5322 simplified regex for email validation
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def __init__(self, firestore_client: firestore.Client):
        """
        Initialize validator with Firestore client.
        
        Args:
            firestore_client: Firestore client for DB queries
        """
        self.db = firestore_client
    
    def validate(self, email: str, last_name: Optional[str] = None) -> ValidationResult:
        """
        Validates email format and checks if user exists.
        
        Args:
            email: Email address to validate
            last_name: Optional last name for returning user check
        
        Returns:
            ValidationResult with:
            - success: True if valid format
            - data: {
                "email": cleaned email,
                "is_returning_user": bool,
                "user_data": {...} if returning user
              }
            - error_message: Error if validation failed
        """
        
        # Step 1: Clean and normalize email
        email = email.strip().lower()
        
        # Step 2: Validate format
        if not self._is_valid_format(email):
            return ValidationResult(
                success=False,
                error_message="That doesn't look like a valid email address. Please check and try again."
            )
        
        # Step 3: Check for returning user (if last_name provided)
        user_data = None
        is_returning = False
        
        if last_name:
            user_data = self._check_returning_user(email, last_name)
            is_returning = user_data is not None
        
        # Step 4: Return result
        return ValidationResult(
            success=True,
            data={
                "email": email,
                "is_returning_user": is_returning,
                "user_data": user_data
            },
            metadata={
                "validation_type": "email",
                "returning_user_check": last_name is not None
            }
        )
    
    def _is_valid_format(self, email: str) -> bool:
        """
        Validates email format using regex.
        
        Args:
            email: Email to validate
        
        Returns:
            True if valid format, False otherwise
        """
        if not email:
            return False
        
        # Basic checks
        if len(email) > 320:  # RFC 5321 max length
            return False
        
        if email.count('@') != 1:
            return False
        
        # Regex validation
        return self.EMAIL_REGEX.match(email) is not None
    
    def _check_returning_user(self, email: str, last_name: str) -> Optional[dict]:
        """
        Checks if user exists in database with matching email and last_name.
        
        Args:
            email: User's email
            last_name: User's last name
        
        Returns:
            User data dict if found, None otherwise
        """
        try:
            # Query Firestore: users collection
            # Filter: email == email AND last_name == last_name
            users_ref = self.db.collection('users')
            
            query = users_ref.where('email', '==', email)\
                            .where('last_name', '==', last_name)\
                            .limit(1)
            
            results = list(query.stream())
            
            if results:
                user_doc = results[0]
                user_data = user_doc.to_dict()
                
                logger.info(f"Returning user found: {email}")
                
                return {
                    "user_id": user_doc.id,
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "phone": user_data.get("phone"),
                    "country_code": user_data.get("country_code"),
                    "verified": user_data.get("verified", False)
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error checking returning user: {e}")
            return None
    
    def extract_email_from_text(self, text: str) -> Optional[str]:
        """
        Extracts email address from natural language text.
        
        Examples:
        - "my email is john@example.com" → "john@example.com"
        - "contact me at john.doe@company.co.uk" → "john.doe@company.co.uk"
        
        Args:
            text: Text that may contain an email
        
        Returns:
            Extracted email if found, None otherwise
        """
        # Use a regex pattern WITHOUT anchors for extraction
        # This allows finding emails embedded in text
        extraction_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # Find all email-like patterns in text
        matches = re.findall(extraction_pattern, text)
        
        if matches:
            # Return first valid email found (lowercased)
            return matches[0].lower()
        
        return None
