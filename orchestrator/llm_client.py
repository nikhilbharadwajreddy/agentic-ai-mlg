"""
LLM Client Module

Handles all interactions with Vertex AI (Gemini).
Includes function calling for structured extraction and tool execution.
"""

import logging
from typing import List, Dict, Any, Optional
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    Content,
    Part,
    Tool,
    FunctionDeclaration,
)

from .models import LLMMessage, ToolCall

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Wrapper around Vertex AI Gemini for LLM operations.
    """
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        Initialize Vertex AI client.
        
        Why use Vertex AI:
        - Data stays in your GCP project (no external API)
        - CMEK encryption support
        - No data used for training by default
        - SLA and enterprise support
        """
        self.project_id = project_id
        self.location = location
        
        vertexai.init(project=project_id, location=location)
        
        # Use Gemini 2.0 Flash for best results
        self.model = GenerativeModel("gemini-2.0-flash-001")
        
        # Default generation config
        self.generation_config = GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=2048,
        )
    
    def extract_structured_data(
        self,
        messages: List[LLMMessage],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Uses function calling to extract structured data from user message.
        
        Why: Instead of parsing free-form LLM text, we get JSON directly.
        This is critical for workflow enforcement - we need deterministic extraction.
        
        Example:
        User: "My name is John Smith"
        Schema: {"name": "string"}
        Returns: {"name": "John Smith"}
        """
        
        # Define a function that represents our desired output schema
        function_declaration = FunctionDeclaration(
            name="extract_data",
            description="Extract structured information from the user's message",
            parameters={
                "type": "object",
                "properties": schema,
                "required": list(schema.keys())
            }
        )
        
        tool = Tool(function_declarations=[function_declaration])
        
        # Convert our messages to Vertex AI format
        contents = self._convert_messages(messages)
        
        try:
            response = self.model.generate_content(
                contents,
                tools=[tool],
                generation_config=self.generation_config,
            )
            
            # Extract function call from response
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        return dict(part.function_call.args)
            
            return {}
        
        except Exception as e:
            logger.error(f"Structured extraction failed: {e}")
            return {}
    
    def generate_response(
        self,
        context: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generates natural conversational response based on context.
        
        This is the NEW architecture method - used AFTER validation succeeds.
        Creates natural, contextual responses instead of hardcoded strings.
        
        Args:
            context: Dictionary with context about current step, user data, etc.
            system_prompt: Optional custom system prompt
        
        Returns:
            Natural language response string
        
        Example:
            context = {
                "step": "name_collected",
                "first_name": "John",
                "last_name": "Smith"
            }
            → "Great to meet you, John Smith! Now, could you please provide your email address?"
        """
        
        # Build system instruction based on context
        if not system_prompt:
            system_prompt = self._build_system_prompt_from_context(context)
        
        # Create user message for response generation
        user_message = self._build_user_message_from_context(context)
        
        try:
            # Combine system prompt and user message into a single prompt
            full_prompt = f"{system_prompt}\n\n{user_message}"
            
            # Use model's generate_content directly
            response = self.model.generate_content(
                full_prompt,
                generation_config=self.generation_config,
            )
            
            return response.text
        
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # Fallback to context-based response
            return self._fallback_response(context)
    
    def chat(
        self,
        messages: List[LLMMessage],
        available_tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        General chat completion with optional tool calling.
        
        Why separate from extract_structured_data:
        - This is for conversational responses
        - extract_structured_data is for deterministic extraction
        
        Note: System instructions should be included in the messages list
        with role="system". They will be converted to proper format by _convert_messages.
        """
        
        # Convert messages - system message goes first if present
        contents = self._convert_messages(messages)
        
        # Use default model
        model_to_use = self.model
        
        # Add tools if provided
        tools = None
        if available_tools:
            function_declarations = [
                FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=tool.get("parameters", {})
                )
                for tool in available_tools
            ]
            tools = [Tool(function_declarations=function_declarations)]
        
        try:
            response = model_to_use.generate_content(
                contents,
                tools=tools,
                generation_config=self.generation_config,
            )
            
            # Check if LLM wants to call a tool
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        # Return indication that tool call is needed
                        return f"TOOL_CALL:{part.function_call.name}:{dict(part.function_call.args)}"
            
            # Return text response
            return response.text
        
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return "I apologize, but I'm having trouble processing your request right now."
    
    def _convert_messages(self, messages: List[LLMMessage]) -> List[Content]:
        """
        Converts our internal message format to Vertex AI format.
        System messages are converted to user messages with a prefix.
        """
        contents = []
        
        for msg in messages:
            # Vertex AI Gemini uses 'user' and 'model' roles
            # System messages become user messages with context
            if msg.role == "system":
                # Convert system message to user message with instruction prefix
                contents.append(
                    Content(
                        role="user",
                        parts=[Part.from_text(f"[SYSTEM INSTRUCTION]: {msg.content}")]
                    )
                )
            else:
                role = "user" if msg.role == "user" else "model"
                contents.append(
                    Content(
                        role=role,
                        parts=[Part.from_text(msg.content)]
                    )
                )
        
        return contents
    
    def _build_system_prompt_from_context(self, context: Dict[str, Any]) -> str:
        """
        Builds system prompt based on context.
        
        Args:
            context: Context dictionary
        
        Returns:
            System prompt string
        """
        base_prompt = """You are a friendly, professional AI assistant helping users through a verification process.

Your role:
- Guide users through collecting their information (name, email, phone)
- Be warm, conversational, and helpful
- Keep responses concise (1-2 sentences)
- Never ask for information already collected
- Be encouraging and positive

Tone: Professional but friendly, like a helpful receptionist."""
        
        step = context.get("step", "")
        
        # Add step-specific guidance
        step_prompts = {
            "terms_accepted": "\nUser just accepted terms. Welcome them and ask for their name naturally.",
            "name_incomplete": "\nUser provided only first name. Politely ask for their full name (first and last).",
            "name_collected": "\nUser just provided their full name. Thank them and ask for their email address.",
            "email_collected": "\nUser just provided their email. Acknowledge it and ask for their phone number with country code.",
            "email_returning_user": "\nThis is a returning user. Welcome them back warmly and confirm their saved phone number.",
            "phone_collected": "\nUser just provided their phone. Confirm you'll send a verification code to their email.",
            "otp_sent": "\nVerification code was sent to their email. Ask them to enter the code.",
            "otp_invalid": "\nUser entered wrong OTP code. Encourage them to try again.",
            "otp_verified": "\nUser successfully verified! Welcome them and ask how you can help.",
            "active": "\nUser is fully verified and can use all features. Be helpful and respond to their requests."
        }
        
        if step in step_prompts:
            base_prompt += step_prompts[step]
        
        return base_prompt
    
    def _build_user_message_from_context(self, context: Dict[str, Any]) -> str:
        """
        Builds user message for response generation.
        
        Args:
            context: Context dictionary
        
        Returns:
            User message string
        """
        step = context.get("step", "")
        
        # Include relevant context data
        parts = []
        
        if context.get("first_name"):
            parts.append(f"User's first name: {context['first_name']}")
        
        if context.get("last_name"):
            parts.append(f"User's last name: {context['last_name']}")
        
        if context.get("email"):
            parts.append(f"User's email: {context['email']}")
        
        if context.get("phone_masked"):
            parts.append(f"User's saved phone: {context['phone_masked']}")
        
        if context.get("is_returning_user"):
            parts.append("This is a returning user")
        
        if context.get("error"):
            parts.append(f"Error: {context['error']}")
        
        # Combine context and request
        message = "\n".join(parts) if parts else "No additional context"
        message += f"\n\nGenerate a natural, friendly response for step: {step}"
        
        return message
    
    def _fallback_response(self, context: Dict[str, Any]) -> str:
        """
        Fallback responses if LLM fails.
        
        Args:
            context: Context dictionary
        
        Returns:
            Fallback response string
        """
        step = context.get("step", "")
        
        fallbacks = {
            "terms_accepted": "Thank you for accepting our terms. What's your name?",
            "name_collected": "Great! What's your email address?",
            "email_collected": "Perfect! Now I need your phone number with country code.",
            "phone_collected": "I've sent a verification code to your email. Please enter it here.",
            "otp_verified": "Verification complete! How can I help you today?",
            "active": "How can I assist you today?"
        }
        
        return fallbacks.get(step, "How can I help you?")
    
    def validate_response_safety(self, text: str) -> bool:
        """
        Checks if response contains any unsafe content.
        
        Why: Even though Vertex AI has built-in safety filters,
        we add an extra layer to check for leaked secrets or PII.
        """
        
        # Simple heuristics - in production, use more sophisticated checks
        unsafe_patterns = [
            "password",
            "api_key",
            "secret",
            "token",
            "ssn",
        ]
        
        text_lower = text.lower()
        for pattern in unsafe_patterns:
            if pattern in text_lower:
                logger.warning(f"Potential unsafe content detected: {pattern}")
                return False
        
        return True
