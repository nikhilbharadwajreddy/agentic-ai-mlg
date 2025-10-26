"""
Appointment Service

Handles Firestore CRUD operations for appointments and availability slots.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from google.cloud import firestore

logger = logging.getLogger(__name__)


class AppointmentService:
    """
    Service layer for appointment and availability management.
    
    Collections:
    - availability_slots: Time slots that can be booked
    - appointments: Actual bookings made by users
    """
    
    def __init__(self, db_client: firestore.Client):
        """
        Initialize appointment service.
        
        Args:
            db_client: Firestore client
        """
        self.db = db_client
        self.slots_collection = self.db.collection("availability_slots")
        self.appointments_collection = self.db.collection("appointments")
    
    # ============= AVAILABILITY SLOTS =============
    
    def get_available_slots(
        self, 
        date: str, 
        service_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available time slots for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
            service_type: Optional filter by service type
            
        Returns:
            List of available slot dictionaries
        """
        try:
            query = self.slots_collection.where("date", "==", date)\
                                         .where("status", "==", "available")\
                                         .order_by("time")
            
            if service_type:
                query = query.where("service_type", "==", service_type)
            
            slots = []
            for doc in query.stream():
                slot_data = doc.to_dict()
                slot_data["slot_id"] = doc.id
                slots.append(slot_data)
            
            logger.info(f"Found {len(slots)} available slots for {date}")
            return slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []
    
    def get_slot_by_id(self, slot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific slot by ID.
        
        Args:
            slot_id: Slot document ID
            
        Returns:
            Slot data or None if not found
        """
        try:
            doc = self.slots_collection.document(slot_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["slot_id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Error getting slot {slot_id}: {e}")
            return None
    
    def mark_slot_booked(self, slot_id: str) -> bool:
        """
        Mark a slot as booked.
        
        Args:
            slot_id: Slot document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.slots_collection.document(slot_id).update({
                "status": "booked",
                "booked_at": datetime.now(timezone.utc)
            })
            logger.info(f"Slot {slot_id} marked as booked")
            return True
        except Exception as e:
            logger.error(f"Error marking slot {slot_id} as booked: {e}")
            return False
    
    def mark_slot_available(self, slot_id: str) -> bool:
        """
        Mark a slot as available (for cancellations).
        
        Args:
            slot_id: Slot document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.slots_collection.document(slot_id).update({
                "status": "available",
                "booked_at": firestore.DELETE_FIELD
            })
            logger.info(f"Slot {slot_id} marked as available")
            return True
        except Exception as e:
            logger.error(f"Error marking slot {slot_id} as available: {e}")
            return False
    
    # ============= APPOINTMENTS =============
    
    def create_appointment(self, appointment_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new appointment with transaction to prevent double-booking.
        
        Args:
            appointment_data: Appointment details
            
        Returns:
            Appointment ID if successful, None otherwise
        """
        try:
            # Transaction to ensure atomic booking
            transaction = self.db.transaction()
            
            @firestore.transactional
            def create_in_transaction(transaction, appointment_data):
                # Check slot is still available
                slot_ref = self.slots_collection.document(appointment_data["slot_id"])
                slot = slot_ref.get(transaction=transaction)
                
                if not slot.exists:
                    raise ValueError("Slot not found")
                
                slot_data = slot.to_dict()
                if slot_data.get("status") != "available":
                    raise ValueError("Slot no longer available")
                
                # Create appointment
                appointment_ref = self.appointments_collection.document()
                appointment_data["appointment_id"] = appointment_ref.id
                appointment_data["booked_at"] = datetime.now(timezone.utc)
                appointment_data["status"] = "confirmed"
                
                transaction.set(appointment_ref, appointment_data)
                
                # Mark slot as booked
                transaction.update(slot_ref, {
                    "status": "booked",
                    "booked_at": datetime.now(timezone.utc)
                })
                
                return appointment_ref.id
            
            appointment_id = create_in_transaction(transaction, appointment_data)
            logger.info(f"Appointment {appointment_id} created successfully")
            return appointment_id
            
        except ValueError as e:
            logger.warning(f"Appointment creation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return None
    
    def get_user_appointments(
        self, 
        user_id: str, 
        include_past: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get appointments for a specific user.
        
        Args:
            user_id: User's ID
            include_past: Whether to include past appointments
            
        Returns:
            List of appointment dictionaries
        """
        try:
            query = self.appointments_collection.where("user_id", "==", user_id)\
                                                .where("status", "==", "confirmed")\
                                                .order_by("date")\
                                                .order_by("time")
            
            appointments = []
            today = datetime.now(timezone.utc).date().isoformat()
            
            for doc in query.stream():
                appt_data = doc.to_dict()
                appt_data["appointment_id"] = doc.id
                
                # Filter past appointments if needed
                if not include_past and appt_data.get("date", "") < today:
                    continue
                
                appointments.append(appt_data)
            
            logger.info(f"Found {len(appointments)} appointments for user {user_id}")
            return appointments
            
        except Exception as e:
            logger.error(f"Error getting user appointments: {e}")
            return []
    
    def get_appointment_by_id(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific appointment by ID.
        
        Args:
            appointment_id: Appointment document ID
            
        Returns:
            Appointment data or None if not found
        """
        try:
            doc = self.appointments_collection.document(appointment_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["appointment_id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Error getting appointment {appointment_id}: {e}")
            return None
    
    def cancel_appointment(self, appointment_id: str, user_id: str) -> bool:
        """
        Cancel an appointment and free up the slot.
        
        Args:
            appointment_id: Appointment document ID
            user_id: User ID (for verification)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get appointment
            appt = self.get_appointment_by_id(appointment_id)
            if not appt:
                logger.warning(f"Appointment {appointment_id} not found")
                return False
            
            # Verify ownership
            if appt.get("user_id") != user_id:
                logger.warning(f"User {user_id} does not own appointment {appointment_id}")
                return False
            
            # Transaction to cancel appointment and free slot
            transaction = self.db.transaction()
            
            @firestore.transactional
            def cancel_in_transaction(transaction, appointment_id, slot_id):
                # Update appointment status
                appt_ref = self.appointments_collection.document(appointment_id)
                transaction.update(appt_ref, {
                    "status": "cancelled",
                    "cancelled_at": datetime.now(timezone.utc)
                })
                
                # Mark slot as available
                slot_ref = self.slots_collection.document(slot_id)
                transaction.update(slot_ref, {
                    "status": "available",
                    "booked_at": firestore.DELETE_FIELD
                })
            
            cancel_in_transaction(transaction, appointment_id, appt["slot_id"])
            logger.info(f"Appointment {appointment_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling appointment {appointment_id}: {e}")
            return False
    
    # ============= ADMIN FUNCTIONS =============
    
    def create_slot(self, slot_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new availability slot (admin function).
        
        Args:
            slot_data: Slot details
            
        Returns:
            Slot ID if successful, None otherwise
        """
        try:
            slot_data["status"] = "available"
            slot_data["created_at"] = datetime.now(timezone.utc)
            
            doc_ref = self.slots_collection.add(slot_data)
            slot_id = doc_ref[1].id
            
            logger.info(f"Slot {slot_id} created for {slot_data.get('date')} {slot_data.get('time')}")
            return slot_id
            
        except Exception as e:
            logger.error(f"Error creating slot: {e}")
            return None
    
    def get_all_appointments(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all appointments (admin function).
        
        Args:
            date: Optional date filter
            
        Returns:
            List of appointments
        """
        try:
            query = self.appointments_collection.where("status", "==", "confirmed")
            
            if date:
                query = query.where("date", "==", date)
            
            query = query.order_by("date").order_by("time")
            
            appointments = []
            for doc in query.stream():
                appt_data = doc.to_dict()
                appt_data["appointment_id"] = doc.id
                appointments.append(appt_data)
            
            return appointments
            
        except Exception as e:
            logger.error(f"Error getting all appointments: {e}")
            return []
