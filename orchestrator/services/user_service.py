"""
User Service

Handles user CRUD operations in Firestore.

Features:
- Create new users after verification
- Find existing users (returning user check)
- Update user information
- Track last login
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from google.cloud import firestore

from ..models import User

logger = logging.getLogger(__name__)


class UserService:
    """
    Manages user data in Firestore 'users' collection.
    
    Collection structure:
    users/
      {user_id}/
        - email
        - first_name
        - last_name
        - phone
        - country_code
        - verified
        - created_at
        - last_login
    """
    
    def __init__(self, firestore_client: firestore.Client):
        """
        Initialize user service.
        
        Args:
            firestore_client: Firestore client instance
        """
        self.db = firestore_client
        self.collection = self.db.collection('users')
    
    def create_user(self, user: User) -> bool:
        """
        Creates a new user in Firestore.
        
        Args:
            user: User model with all data
        
        Returns:
            True if created successfully, False otherwise
        """
        try:
            user_dict = user.model_dump()
            
            # Set document with user_id as document ID
            self.collection.document(user.user_id).set(user_dict)
            
            logger.info(f"User created: {user.email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create user {user.email}: {e}")
            return False
    
    def find_by_email_and_lastname(
        self,
        email: str,
        last_name: str
    ) -> Optional[User]:
        """
        Finds user by email and last name (for returning user detection).
        
        This query uses composite index: email + last_name
        
        Args:
            email: User's email
            last_name: User's last name
        
        Returns:
            User object if found, None otherwise
        """
        try:
            # Query with composite index
            query = self.collection\
                .where('email', '==', email.lower())\
                .where('last_name', '==', last_name)\
                .limit(1)
            
            results = list(query.stream())
            
            if results:
                user_doc = results[0]
                user_data = user_doc.to_dict()
                
                # Convert to User model
                user = User(**user_data)
                
                logger.info(f"Returning user found: {email}")
                return user
            
            logger.info(f"No existing user found for: {email}")
            return None
        
        except Exception as e:
            logger.error(f"Error finding user by email/lastname: {e}")
            return None
    
    def find_by_user_id(self, user_id: str) -> Optional[User]:
        """
        Finds user by user_id.
        
        Args:
            user_id: User's unique ID
        
        Returns:
            User object if found, None otherwise
        """
        try:
            doc = self.collection.document(user_id).get()
            
            if doc.exists:
                user_data = doc.to_dict()
                return User(**user_data)
            
            return None
        
        except Exception as e:
            logger.error(f"Error finding user by ID {user_id}: {e}")
            return None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """
        Finds user by email only.
        
        Args:
            email: User's email
        
        Returns:
            User object if found, None otherwise
        """
        try:
            query = self.collection\
                .where('email', '==', email.lower())\
                .limit(1)
            
            results = list(query.stream())
            
            if results:
                user_doc = results[0]
                user_data = user_doc.to_dict()
                return User(**user_data)
            
            return None
        
        except Exception as e:
            logger.error(f"Error finding user by email: {e}")
            return None
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Updates user fields.
        
        Args:
            user_id: User's ID
            updates: Dictionary of fields to update
        
        Returns:
            True if updated successfully
        """
        try:
            self.collection.document(user_id).update(updates)
            
            logger.info(f"User {user_id} updated: {list(updates.keys())}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            return False
    
    def update_last_login(self, user_id: str) -> bool:
        """
        Updates user's last login timestamp.
        
        Args:
            user_id: User's ID
        
        Returns:
            True if updated successfully
        """
        return self.update_user(user_id, {
            'last_login': datetime.utcnow()
        })
    
    def verify_user(self, user_id: str) -> bool:
        """
        Marks user as verified (after OTP confirmation).
        
        Args:
            user_id: User's ID
        
        Returns:
            True if updated successfully
        """
        return self.update_user(user_id, {
            'verified': True
        })
    
    def update_phone(self, user_id: str, phone: str, country_code: str) -> bool:
        """
        Updates user's phone number.
        
        Args:
            user_id: User's ID
            phone: New phone number (E.164 format)
            country_code: Country calling code
        
        Returns:
            True if updated successfully
        """
        return self.update_user(user_id, {
            'phone': phone,
            'country_code': country_code
        })
    
    def delete_user(self, user_id: str) -> bool:
        """
        Deletes a user (for GDPR compliance / account deletion).
        
        Args:
            user_id: User's ID
        
        Returns:
            True if deleted successfully
        """
        try:
            self.collection.document(user_id).delete()
            
            logger.info(f"User {user_id} deleted")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            return False
    
    def user_exists(self, email: str) -> bool:
        """
        Checks if user with email exists.
        
        Args:
            email: Email to check
        
        Returns:
            True if exists, False otherwise
        """
        user = self.find_by_email(email)
        return user is not None
    
    def get_user_count(self) -> int:
        """
        Gets total number of users (for analytics).
        
        Returns:
            Number of users
        """
        try:
            # This is not efficient for large collections
            # In production, use Firestore aggregation queries
            users = list(self.collection.stream())
            return len(users)
        
        except Exception as e:
            logger.error(f"Failed to get user count: {e}")
            return 0
