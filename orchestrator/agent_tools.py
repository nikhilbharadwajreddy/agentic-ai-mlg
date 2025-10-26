"""
Agent Tools - Functions called by ADK Agent

These are simple Python functions that the agent can call.
"""

import os
from google.cloud import firestore


# Initialize Firestore once
_db = None

def _get_db():
    """Get Firestore client."""
    global _db
    if _db is None:
        project_id = os.getenv("GCP_PROJECT_ID", "agentic-ai-mlg")
        _db = firestore.Client(project=project_id)
    return _db


def list_employees() -> dict:
    """
    Get list of available financial advisors.
    
    Returns:
        dict: List of available advisors with their names and roles.
    """
    try:
        db = _get_db()
        employees = db.collection('employees').where('active', '==', True).stream()
        
        result = []
        for emp in employees:
            data = emp.to_dict()
            result.append({
                "id": data['employee_id'],
                "name": data['name'],
                "role": data['role']
            })
        
        return {"employees": result}
    except Exception as e:
        return {"error": str(e)}


def get_employee_availability(employee_id: str, date: str = None) -> dict:
    """
    Get available time slots for a financial advisor.
    
    Args:
        employee_id: ID of the advisor (required)
        date: Date in YYYY-MM-DD format (optional)
    
    Returns:
        dict: Available time slots for the advisor.
    """
    try:
        db = _get_db()
        query = db.collection('time_slots')\
            .where('employee_id', '==', employee_id)\
            .where('is_booked', '==', False)
        
        if date:
            query = query.where('date', '==', date)
        
        slots = query.stream()
        
        result = []
        for slot in slots:
            data = slot.to_dict()
            result.append({
                "date": data['date'],
                "start_time": data['start_time'],
                "end_time": data['end_time']
            })
        
        return {"slots": result}
    except Exception as e:
        return {"error": str(e)}


def book_appointment(
    employee_id: str,
    date: str,
    time: str,
    customer_id: str = "unknown",
    customer_name: str = "Customer",
    customer_email: str = "customer@example.com"
) -> dict:
    """
    Book an appointment with a financial advisor.
    
    Args:
        employee_id: ID of the advisor to meet with (required)
        date: Date in YYYY-MM-DD format (required)
        time: Time in HH:MM format 24-hour (required)
        customer_id: Customer's user ID
        customer_name: Customer's name
        customer_email: Customer's email
    
    Returns:
        dict: Booking confirmation with appointment details.
    """
    try:
        db = _get_db()
        
        # Get employee name
        emp_doc = db.collection('employees').document(employee_id).get()
        if not emp_doc.exists:
            return {"error": "Advisor not found"}
        
        employee_name = emp_doc.to_dict()['name']
        
        # Create appointment
        import uuid
        appointment_id = f"apt_{uuid.uuid4().hex[:8]}"
        
        appointment = {
            "appointment_id": appointment_id,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "employee_id": employee_id,
            "employee_name": employee_name,
            "date": date,
            "time": time,
            "purpose": "Financial Consultation",
            "status": "confirmed",
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        db.collection('appointments').document(appointment_id).set(appointment)
        
        # Mark slot as booked
        slots = db.collection('time_slots')\
            .where('employee_id', '==', employee_id)\
            .where('date', '==', date)\
            .where('start_time', '==', time)\
            .where('is_booked', '==', False)\
            .limit(1).stream()
        
        for slot in slots:
            slot.reference.update({'is_booked': True})
        
        return {
            "success": True,
            "appointment_id": appointment_id,
            "message": f"Appointment booked with {employee_name} on {date} at {time}"
        }
    except Exception as e:
        return {"error": str(e)}
