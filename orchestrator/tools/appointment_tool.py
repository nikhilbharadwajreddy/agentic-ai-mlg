"""
Appointment Tool

Implements appointment booking functionality for the AI agent.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

from ..services.appointment_service import AppointmentService
from ..services.email_service import EmailService

logger = logging.getLogger(__name__)


class AppointmentTool:
    """
    Tool for managing appointments.
    
    Functions:
    - check_availability: Show available time slots
    - book_appointment: Book a specific slot
    - list_appointments: Show user's appointments
    - cancel_appointment: Cancel a booking
    """
    
    # Service types configuration
    SERVICE_TYPES = {
        "consultation": {
            "name": "Consultation",
            "duration": 30,
            "description": "30-minute consultation to discuss your needs"
        },
        "demo": {
            "name": "Product Demo",
            "duration": 45,
            "description": "45-minute product demonstration"
        },
        "support": {
            "name": "Technical Support",
            "duration": 30,
            "description": "30-minute technical support session"
        }
    }
    
    def __init__(self, appointment_service: AppointmentService, email_service: EmailService):
        """
        Initialize appointment tool.
        
        Args:
            appointment_service: Service for Firestore operations
            email_service: Service for sending emails
        """
        self.appointment_service = appointment_service
        self.email_service = email_service
    
    def check_availability(
        self, 
        date: str,
        service_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check available time slots for a date.
        
        Args:
            date: Date in YYYY-MM-DD format
            service_type: Optional service type filter
            
        Returns:
            Dictionary with available slots
        """
        try:
            # Validate date
            if not self._is_valid_date(date):
                return {
                    "success": False,
                    "error": "Invalid date format. Please use YYYY-MM-DD"
                }
            
            # Validate service type
            if service_type and service_type not in self.SERVICE_TYPES:
                return {
                    "success": False,
                    "error": f"Invalid service type. Choose from: {', '.join(self.SERVICE_TYPES.keys())}"
                }
            
            # Get available slots
            slots = self.appointment_service.get_available_slots(date, service_type)
            
            if not slots:
                return {
                    "success": True,
                    "available": False,
                    "message": f"No available slots for {date}",
                    "slots": []
                }
            
            # Format slots for display
            formatted_slots = []
            for slot in slots:
                formatted_slots.append({
                    "slot_id": slot["slot_id"],
                    "time": slot["time"],
                    "service_type": slot.get("service_type", "consultation"),
                    "service_name": self.SERVICE_TYPES.get(
                        slot.get("service_type", "consultation"), {}
                    ).get("name", "Consultation"),
                    "duration_minutes": slot.get("duration_minutes", 30)
                })
            
            return {
                "success": True,
                "available": True,
                "date": date,
                "slots": formatted_slots,
                "count": len(formatted_slots)
            }
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {
                "success": False,
                "error": "Failed to check availability"
            }
    
    def book_appointment(
        self,
        slot_id: str,
        user_id: str,
        user_name: str,
        user_email: str,
        user_phone: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Book an appointment.
        
        Args:
            slot_id: ID of the slot to book
            user_id: User's ID
            user_name: User's full name
            user_email: User's email
            user_phone: User's phone
            notes: Optional notes
            
        Returns:
            Dictionary with booking result
        """
        try:
            # Get slot details
            slot = self.appointment_service.get_slot_by_id(slot_id)
            if not slot:
                return {
                    "success": False,
                    "error": "Slot not found"
                }
            
            if slot.get("status") != "available":
                return {
                    "success": False,
                    "error": "This time slot is no longer available"
                }
            
            # Prepare appointment data
            appointment_data = {
                "slot_id": slot_id,
                "user_id": user_id,
                "user_name": user_name,
                "user_email": user_email,
                "phone": user_phone,
                "date": slot["date"],
                "time": slot["time"],
                "service_type": slot.get("service_type", "consultation"),
                "duration_minutes": slot.get("duration_minutes", 30),
                "notes": notes
            }
            
            # Create appointment (with transaction)
            appointment_id = self.appointment_service.create_appointment(appointment_data)
            
            if not appointment_id:
                return {
                    "success": False,
                    "error": "Failed to book appointment. Slot may have been booked by someone else."
                }
            
            # Send confirmation email
            service_info = self.SERVICE_TYPES.get(slot.get("service_type", "consultation"), {})
            self._send_confirmation_email(
                user_email,
                user_name,
                appointment_id,
                slot["date"],
                slot["time"],
                service_info
            )
            
            return {
                "success": True,
                "appointment_id": appointment_id,
                "date": slot["date"],
                "time": slot["time"],
                "service_type": slot.get("service_type", "consultation"),
                "service_name": service_info.get("name", "Consultation"),
                "duration_minutes": slot.get("duration_minutes", 30),
                "message": f"Appointment booked successfully! Confirmation sent to {user_email}"
            }
            
        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return {
                "success": False,
                "error": "Failed to book appointment"
            }
    
    def list_appointments(self, user_id: str) -> Dict[str, Any]:
        """
        List user's upcoming appointments.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dictionary with appointments
        """
        try:
            appointments = self.appointment_service.get_user_appointments(user_id)
            
            if not appointments:
                return {
                    "success": True,
                    "has_appointments": False,
                    "message": "You have no upcoming appointments",
                    "appointments": []
                }
            
            # Format appointments
            formatted_appointments = []
            for appt in appointments:
                service_info = self.SERVICE_TYPES.get(appt.get("service_type", "consultation"), {})
                formatted_appointments.append({
                    "appointment_id": appt["appointment_id"],
                    "date": appt["date"],
                    "time": appt["time"],
                    "service_name": service_info.get("name", "Consultation"),
                    "duration_minutes": appt.get("duration_minutes", 30),
                    "notes": appt.get("notes", "")
                })
            
            return {
                "success": True,
                "has_appointments": True,
                "count": len(formatted_appointments),
                "appointments": formatted_appointments
            }
            
        except Exception as e:
            logger.error(f"Error listing appointments: {e}")
            return {
                "success": False,
                "error": "Failed to retrieve appointments"
            }
    
    def cancel_appointment(
        self, 
        appointment_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Cancel an appointment.
        
        Args:
            appointment_id: Appointment ID
            user_id: User's ID (for verification)
            
        Returns:
            Dictionary with cancellation result
        """
        try:
            # Get appointment details first
            appt = self.appointment_service.get_appointment_by_id(appointment_id)
            if not appt:
                return {
                    "success": False,
                    "error": "Appointment not found"
                }
            
            # Cancel appointment
            success = self.appointment_service.cancel_appointment(appointment_id, user_id)
            
            if not success:
                return {
                    "success": False,
                    "error": "Failed to cancel appointment. Please verify the appointment ID."
                }
            
            # Send cancellation email
            self._send_cancellation_email(
                appt["user_email"],
                appt["user_name"],
                appointment_id,
                appt["date"],
                appt["time"]
            )
            
            return {
                "success": True,
                "message": f"Appointment on {appt['date']} at {appt['time']} has been cancelled",
                "date": appt["date"],
                "time": appt["time"]
            }
            
        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            return {
                "success": False,
                "error": "Failed to cancel appointment"
            }
    
    # Helper methods
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Validate date format and ensure it's not in the past"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = datetime.now(timezone.utc).date()
            return date_obj >= today
        except ValueError:
            return False
    
    def _send_confirmation_email(
        self, 
        email: str,
        name: str,
        appointment_id: str,
        date: str,
        time: str,
        service_info: Dict[str, Any]
    ):
        """Send appointment confirmation email"""
        try:
            subject = f"Appointment Confirmed - {date} at {time}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4A90E2;">Appointment Confirmed ✅</h2>
                    
                    <p>Hi {name},</p>
                    
                    <p>Your appointment has been successfully booked!</p>
                    
                    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Appointment Details:</h3>
                        <p><strong>Service:</strong> {service_info.get('name', 'Consultation')}</p>
                        <p><strong>Date:</strong> {date}</p>
                        <p><strong>Time:</strong> {time}</p>
                        <p><strong>Duration:</strong> {service_info.get('duration', 30)} minutes</p>
                        <p><strong>Appointment ID:</strong> {appointment_id}</p>
                    </div>
                    
                    <p>If you need to cancel or reschedule, please let us know at least 24 hours in advance.</p>
                    
                    <p>Looking forward to meeting with you!</p>
                    
                    <p>Best regards,<br>
                    The MLGround Team</p>
                </div>
            </body>
            </html>
            """
            
            self.email_service.send_email(
                to_email=email,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")
    
    def _send_cancellation_email(
        self,
        email: str,
        name: str,
        appointment_id: str,
        date: str,
        time: str
    ):
        """Send appointment cancellation email"""
        try:
            subject = f"Appointment Cancelled - {date} at {time}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #E74C3C;">Appointment Cancelled</h2>
                    
                    <p>Hi {name},</p>
                    
                    <p>Your appointment has been cancelled as requested.</p>
                    
                    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Date:</strong> {date}</p>
                        <p><strong>Time:</strong> {time}</p>
                        <p><strong>Appointment ID:</strong> {appointment_id}</p>
                    </div>
                    
                    <p>If you'd like to book a new appointment, just let us know!</p>
                    
                    <p>Best regards,<br>
                    The MLGround Team</p>
                </div>
            </body>
            </html>
            """
            
            self.email_service.send_email(
                to_email=email,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send cancellation email: {e}")
