"""
Admin Service

Manages employees, availability, and appointments.
Super admin operations.
"""

import logging
import uuid
from typing import List, Optional
from datetime import datetime
from google.cloud import firestore

from ..appointment_models import Employee, TimeSlot, Appointment

logger = logging.getLogger(__name__)


class AdminService:
    """Handles admin operations for appointment system."""
    
    def __init__(self, firestore_client: firestore.Client):
        self.db = firestore_client
    
    # ===== EMPLOYEE MANAGEMENT =====
    
    def create_employee(self, name: str, role: str, email: str) -> Employee:
        """Add new employee/sales rep."""
        employee_id = f"emp_{uuid.uuid4().hex[:8]}"
        
        employee = Employee(
            employee_id=employee_id,
            name=name,
            role=role,
            email=email
        )
        
        self.db.collection('employees').document(employee_id).set(employee.model_dump())
        logger.info(f"Employee created: {name}")
        return employee
    
    def list_employees(self, active_only: bool = True) -> List[Employee]:
        """Get all employees."""
        query = self.db.collection('employees')
        if active_only:
            query = query.where('active', '==', True)
        
        docs = query.stream()
        return [Employee(**doc.to_dict()) for doc in docs]
    
    def deactivate_employee(self, employee_id: str) -> bool:
        """Deactivate employee."""
        self.db.collection('employees').document(employee_id).update({'active': False})
        return True
    
    # ===== AVAILABILITY MANAGEMENT =====
    
    def add_time_slot(self, employee_id: str, date: str, start_time: str, end_time: str) -> TimeSlot:
        """Add available time slot for employee."""
        slot_id = f"slot_{uuid.uuid4().hex[:8]}"
        
        slot = TimeSlot(
            slot_id=slot_id,
            employee_id=employee_id,
            date=date,
            start_time=start_time,
            end_time=end_time
        )
        
        self.db.collection('time_slots').document(slot_id).set(slot.model_dump())
        logger.info(f"Slot added for {employee_id}: {date} {start_time}")
        return slot
    
    def get_available_slots(self, employee_id: str, date: Optional[str] = None) -> List[TimeSlot]:
        """Get available slots for employee."""
        query = self.db.collection('time_slots')\
            .where('employee_id', '==', employee_id)\
            .where('is_booked', '==', False)
        
        if date:
            query = query.where('date', '==', date)
        
        docs = query.stream()
        return [TimeSlot(**doc.to_dict()) for doc in docs]
    
    def delete_time_slot(self, slot_id: str) -> bool:
        """Remove time slot."""
        self.db.collection('time_slots').document(slot_id).delete()
        return True
    
    # ===== APPOINTMENT MANAGEMENT =====
    
    def book_appointment(
        self,
        customer_id: str,
        customer_name: str,
        customer_email: str,
        employee_id: str,
        date: str,
        time: str
    ) -> Appointment:
        """Book appointment (used by agent)."""
        
        # Get employee name
        emp_doc = self.db.collection('employees').document(employee_id).get()
        employee_name = emp_doc.to_dict()['name'] if emp_doc.exists else "Team Member"
        
        # Create appointment
        appointment_id = f"apt_{uuid.uuid4().hex[:8]}"
        
        appointment = Appointment(
            appointment_id=appointment_id,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            employee_id=employee_id,
            employee_name=employee_name,
            date=date,
            time=time
        )
        
        # Save to Firestore
        self.db.collection('appointments').document(appointment_id).set(appointment.model_dump())
        
        # Mark slot as booked
        slots = self.db.collection('time_slots')\
            .where('employee_id', '==', employee_id)\
            .where('date', '==', date)\
            .where('start_time', '==', time)\
            .where('is_booked', '==', False)\
            .limit(1).stream()
        
        for slot in slots:
            slot.reference.update({'is_booked': True})
        
        logger.info(f"Appointment booked: {appointment_id}")
        return appointment
    
    def get_all_appointments(self, status: Optional[str] = None) -> List[Appointment]:
        """Get all appointments (admin view)."""
        query = self.db.collection('appointments')
        
        if status:
            query = query.where('status', '==', status)
        
        docs = query.order_by('date').order_by('time').stream()
        return [Appointment(**doc.to_dict()) for doc in docs]
    
    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel appointment."""
        apt_ref = self.db.collection('appointments').document(appointment_id)
        apt = apt_ref.get()
        
        if apt.exists:
            apt_data = apt.to_dict()
            apt_ref.update({'status': 'cancelled'})
            
            # Free up the slot
            slots = self.db.collection('time_slots')\
                .where('employee_id', '==', apt_data['employee_id'])\
                .where('date', '==', apt_data['date'])\
                .where('start_time', '==', apt_data['time'])\
                .limit(1).stream()
            
            for slot in slots:
                slot.reference.update({'is_booked': False})
            
            logger.info(f"Appointment cancelled: {appointment_id}")
            return True
        
        return False
