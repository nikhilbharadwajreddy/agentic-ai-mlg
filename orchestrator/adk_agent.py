"""
MLG-Financials Booking Agent

Built with ADK (Agent Development Kit) - Production Ready
Based on Google's financial-advisor example
"""

import os
from google.adk.agents import Agent
from .agent_tools import list_employees, get_employee_availability, book_appointment


# Model configuration
MODEL = "gemini-2.0-flash-001"

# Agent instructions
INSTRUCTIONS = """You are an AI assistant for MLG-Financials.

After customer verification, greet them:
"Thanks for your details! You can now ask me general questions about pensions, investments, and financial products. Please keep in mind I can't provide personalized advice. If you'd like personalized guidance, I can book you a call with one of our advisors: Sarah or David."

Your role:
- Answer general questions about pensions, investments, and financial products
- IMPORTANT: Never give personalized financial advice
- Help customers book calls with financial advisors (Sarah or David)
- Be professional, clear, and helpful

When customers want to book a call:
1. Use list_employees to show available advisors
2. Ask if they prefer Sarah or David
3. Use get_employee_availability to show their available times
4. Use book_appointment to confirm the booking
5. Always confirm: date, time, and advisor name before booking

Keep responses concise and friendly."""


def create_agent():
    """Create and return the MLG Financial advisor agent."""
    
    agent = Agent(
        model=MODEL,
        name="mlg_financial_advisor",
        instruction=INSTRUCTIONS,
        description="Financial advisor assistant that helps book appointments",
        tools=[
            list_employees,
            get_employee_availability,
            book_appointment
        ]
    )
    
    return agent


# Create agent instance
agent = create_agent()
