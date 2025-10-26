"""
Appointments Tool - Sample Tool Implementation

This is an example of how tools are implemented in the system.
Each tool is a Python function that the LLM can call via function calling.

SECURITY FEATURES:
- Only callable by VERIFIED users
- Validates all parameters
- Logs every execution
- Returns structured results
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from orchestrator.models import ToolResult


class AppointmentService:
    """
    Sample appointment scheduling service.
    
    In production, this would:
    - Connect to your calendar API (Google Calendar, Outlook, etc.)
    - Check availability in real-time
    - Send confirmation emails/SMS
    - Store appointments in database
    
    For now, it's a mock implementation for demo purposes.
    """
    
    def __init__(self, firestore_client):
        self.db = firestore_client
    
    # ============================================
    # TOOL: VIEW APPOINTMENTS
    # ============================================
    
    def view_appointments(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> ToolResult:
        """
        View user's appointments within a date range.
        
        Args:
            user_id: User's unique identifier
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
        
        Returns:
            ToolResult with list of appointments
        
        SECURITY: Read-only operation, risk_level = "low"
        """
        try:
            # In production: Query actual calendar/database
            # For demo: Return mock data
            
            appointments = [
                {
                    "id": "appt_001",
                    "title": "Doctor Checkup",
                    "datetime": "2025-10-28 10:00:00",
                    "duration_minutes": 30,
                    "location": "Main St Medical Center",
                    "status": "confirmed"
                },
                {
                    "id": "appt_002",
                    "title": "Team Meeting",
                    "datetime": "2025-10-29 14:00:00",
                    "duration_minutes": 60,
                    "location": "Online - Zoom",
                    "status": "confirmed"
                }
            ]
            
            # Filter by date range if provided
            if start_date or end_date:
                # In production: Filter logic here
                pass
            
            return ToolResult(
                tool_name="view_appointments",
                success=True,
                result={
                    "appointments": appointments,
                    "total_count": len(appointments)
                }
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="view_appointments",
                success=False,
                error=str(e)
            )
    
    # ============================================
    # TOOL: SCHEDULE APPOINTMENT
    # ============================================
    
    def schedule_appointment(
        self,
        user_id: str,
        title: str,
        datetime_str: str,
        duration_minutes: int = 30,
        location: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ToolResult:
        """
        Schedule a new appointment for the user.
        
        Args:
            user_id: User's unique identifier
            title: Appointment title/purpose
            datetime_str: Appointment date/time (YYYY-MM-DD HH:MM format)
            duration_minutes: Length of appointment (default 30 mins)
            location: Where appointment takes place
            notes: Additional notes
        
        Returns:
            ToolResult with appointment confirmation
        
        SECURITY: Modification operation, risk_level = "medium"
        Requires user to be in "ACTIVE" state
        """
        try:
            # Validate datetime format
            try:
                appt_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            except ValueError:
                return ToolResult(
                    tool_name="schedule_appointment",
                    success=False,
                    error="Invalid datetime format. Use YYYY-MM-DD HH:MM"
                )
            
            # Check if datetime is in the future
            if appt_datetime < datetime.now():
                return ToolResult(
                    tool_name="schedule_appointment",
                    success=False,
                    error="Cannot schedule appointments in the past"
                )
            
            # Validate duration (must be between 15 mins and 8 hours)
            if duration_minutes < 15 or duration_minutes > 480:
                return ToolResult(
                    tool_name="schedule_appointment",
                    success=False,
                    error="Duration must be between 15 minutes and 8 hours"
                )
            
            # In production:
            # 1. Check calendar availability
            # 2. Create appointment in calendar system
            # 3. Send confirmation email/SMS
            # 4. Store in database
            
            # For demo: Create mock appointment
            appointment_id = f"appt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            appointment_data = {
                "id": appointment_id,
                "user_id": user_id,
                "title": title,
                "datetime": datetime_str,
                "duration_minutes": duration_minutes,
                "location": location or "To be determined",
                "notes": notes,
                "status": "confirmed",
                "created_at": datetime.now().isoformat()
            }
            
            # Store in Firestore (for demo)
            self.db.collection('appointments').document(appointment_id).set(appointment_data)
            
            return ToolResult(
                tool_name="schedule_appointment",
                success=True,
                result={
                    "appointment": appointment_data,
                    "message": f"Appointment scheduled successfully for {datetime_str}"
                }
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="schedule_appointment",
                success=False,
                error=f"Failed to schedule appointment: {str(e)}"
            )
    
    # ============================================
    # TOOL: CANCEL APPOINTMENT
    # ============================================
    
    def cancel_appointment(
        self,
        user_id: str,
        appointment_id: str,
        reason: Optional[str] = None
    ) -> ToolResult:
        """
        Cancel an existing appointment.
        
        Args:
            user_id: User's unique identifier
            appointment_id: ID of appointment to cancel
            reason: Optional cancellation reason
        
        Returns:
            ToolResult with cancellation confirmation
        
        SECURITY: Modification operation, risk_level = "medium"
        """
        try:
            # In production: 
            # 1. Verify appointment exists and belongs to user
            # 2. Update status in calendar system
            # 3. Send cancellation notification
            # 4. Update database
            
            # For demo: Mock cancellation
            doc_ref = self.db.collection('appointments').document(appointment_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return ToolResult(
                    tool_name="cancel_appointment",
                    success=False,
                    error="Appointment not found"
                )
            
            # Update status
            doc_ref.update({
                "status": "cancelled",
                "cancelled_at": datetime.now().isoformat(),
                "cancellation_reason": reason
            })
            
            return ToolResult(
                tool_name="cancel_appointment",
                success=True,
                result={
                    "appointment_id": appointment_id,
                    "message": "Appointment cancelled successfully"
                }
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="cancel_appointment",
                success=False,
                error=f"Failed to cancel appointment: {str(e)}"
            )
    
    # ============================================
    # TOOL: CHECK AVAILABILITY
    # ============================================
    
    def check_availability(
        self,
        user_id: str,
        date: str,
        duration_minutes: int = 30
    ) -> ToolResult:
        """
        Check available time slots for a given date.
        
        Args:
            user_id: User's unique identifier
            date: Date to check (YYYY-MM-DD format)
            duration_minutes: Desired duration
        
        Returns:
            ToolResult with available time slots
        
        SECURITY: Read-only operation, risk_level = "low"
        """
        try:
            # In production: Query calendar and return actual availability
            
            # For demo: Return mock available slots
            available_slots = [
                {"time": "09:00", "available": True},
                {"time": "10:00", "available": True},
                {"time": "11:00", "available": False},  # Already booked
                {"time": "14:00", "available": True},
                {"time": "15:00", "available": True},
                {"time": "16:00", "available": True}
            ]
            
            return ToolResult(
                tool_name="check_availability",
                success=True,
                result={
                    "date": date,
                    "available_slots": [slot for slot in available_slots if slot["available"]],
                    "total_available": sum(1 for slot in available_slots if slot["available"])
                }
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="check_availability",
                success=False,
                error=f"Failed to check availability: {str(e)}"
            )


# ============================================
# HELPER: Get appointment service instance
# ============================================

def get_appointment_service(firestore_client) -> AppointmentService:
    """
    Factory function to create AppointmentService instance.
    Used by tool registry to instantiate the service.
    """
    return AppointmentService(firestore_client)
