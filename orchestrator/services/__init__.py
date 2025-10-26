"""
Services Module

Contains business logic services that interact with external systems.

Services:
- email_service: SendGrid integration for sending OTP emails
- user_service: User CRUD operations in Firestore
"""

from .email_service import EmailService
from .user_service import UserService

__all__ = [
    "EmailService",
    "UserService",
]
