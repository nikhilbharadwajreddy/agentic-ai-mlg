"""Appointment System Models"""

from datetime import datetime
from pydantic import BaseModel, Field


class Employee(BaseModel):
    """Sales rep/team member who takes appointments."""
    employee_id: str
    name: str
    role: str  # "Sales Rep", "Solutions Architect"
    email: str
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TimeSlot(BaseModel):
    """Single time slot for booking."""
    slot_id: str
    employee_id: str
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM (24hr)
    end_time: str  # HH:MM
    is_booked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Appointment(BaseModel):
    """Booked appointment."""
    appointment_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    employee_id: str
    employee_name: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    purpose: str = "ML Solutions Demo"
    status: str = "confirmed"  # confirmed, cancelled, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
