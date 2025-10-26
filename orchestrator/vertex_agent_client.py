"""
Vertex AI Agent Client using ADK

Deploys ADK agent to Vertex AI Agent Engine for production use.
"""

import logging
from typing import Dict, Any
from vertexai.agent_engines import AdkApp
from .adk_agent import agent

logger = logging.getLogger(__name__)


class VertexAgent:
    """Vertex AI Agent using ADK."""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """Initialize ADK Agent with AdkApp."""
        
        try:
            # Initialize Vertex AI
            from google.cloud import aiplatform
            aiplatform.init(project=project_id, location=location)
            
            # Create ADK app
            self.app = AdkApp(agent=agent)
            
            logger.info("ADK Agent initialized successfully")
        
        except Exception as e:
            logger.error(f"ADK Agent initialization error: {e}", exc_info=True)
            raise
    
    async def send_message(
        self,
        user_id: str,
        message: str,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Send message to ADK agent.
        
        Args:
            user_id: Customer ID
            message: User's message
            context: Customer context (name, email, etc.)
        
        Returns:
            Agent's response text
        """
        
        try:
            # Get or create session
            session = await self._get_or_create_session(user_id)
            
            # Build query parameters
            query_params = {}
            if context:
                # Pass context as parameters to agent
                query_params['customer_id'] = context.get('customer_id', user_id)
                query_params['customer_name'] = context.get('customer_name', '')
                query_params['customer_email'] = context.get('customer_email', '')
            
            # Call agent
            response_text = ""
            async for event in self.app.async_stream_query(
                user_id=user_id,
                session_id=session.id,
                message=message
            ):
                # Extract text from response
                if 'content' in event and 'parts' in event['content']:
                    for part in event['content']['parts']:
                        if 'text' in part:
                            response_text += part['text']
            
            return response_text if response_text else "I'm here to help! What would you like to know?"
        
        except Exception as e:
            logger.error(f"Agent message error: {e}", exc_info=True)
            return "I'm having trouble right now. Please try again."
    
    async def _get_or_create_session(self, user_id: str):
        """Get or create session for user."""
        try:
            # List existing sessions
            sessions = await self.app.async_list_sessions(user_id=user_id)
            if sessions:
                return sessions[0]
        except:
            pass
        
        # Create new session
        return await self.app.async_create_session(user_id=user_id)
