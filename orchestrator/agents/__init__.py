"""
AI Agents Module

Multi-agent system for handling different user intents after verification.

Agents:
- MainAgent: Router that classifies intent and delegates to specialist agents
- AppointmentAgent: Handles appointment booking and management
- CompanyInfoAgent: Answers questions using knowledge base
"""

from .main_agent import MainAgent
from .appointment_agent import AppointmentAgent
from .company_info_agent import CompanyInfoAgent

__all__ = [
    'MainAgent',
    'AppointmentAgent', 
    'CompanyInfoAgent'
]
