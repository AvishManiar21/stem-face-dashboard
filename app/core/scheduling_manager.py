"""
Scheduling Manager Module
Handles appointment booking, cancellation, and schedule grid generation
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import csv

logger = logging.getLogger(__name__)


class SchedulingManager:
    """Manages scheduling operations: booking, cancellation, availability checks"""
    
    def __init__(self, data_dir='data/core'):
        self.data_dir = Path(data_dir)
        self.load_data()
    
    def load_data(self):
        """Reload all CSVs - called on initialization and when CSVs change"""
        try:
            # Load core data files
            self.appointments = self._load_appointments()
            self.tutors = self._load_tutors()
            self.users = self._load_users()
            self.courses = self._load_courses()
            self.shifts = self._load_shifts()
            self.shift_assignments = self._load_shift_assignments()
            self.availability = self._load_availability()
            self.time_slots = self._load_time_slots()
            
            # Merge tutor data with user data for full names
            if not self.tutors.empty and not self.users.empty:
                self.tutors = self.tutors.merge(
                    self.users[['user_id', 'full_name', 'email']], 
                    on='user_id', 
                    how='left'
                )
            
            logger.info("SchedulingManager: Data loaded successfully")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def _load_appointments(self):
        """Load appointments data"""
        try:
            df = pd.read_csv(self.data_dir / 'appointments.csv')
            if not df.empty:
                df['appointment_date'] = pd.to_datetime(df['appointment_date'])
                df['start_time'] = pd.to_datetime(df['start_time'], format='%H:%M:%S', errors='coerce').dt.time
                df['end_time'] = pd.to_datetime(df['end_time'], format='%H:%M:%S', errors='coerce').dt.time
            return df
        except Exception as e:
            logger.error(f"Error loading appointments: {e}")
            return pd.DataFrame()
    
    def _load_tutors(self):
        """Load tutors data"""
        try:
            return pd.read_csv(self.data_dir / 'tutors.csv')
        except Exception as e:
            logger.error(f"Error loading tutors: {e}")
            return pd.DataFrame()
    
    def _load_users(self):
        """Load users data"""
        try:
            return pd.read_csv(self.data_dir / 'users.csv')
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            return pd.DataFrame()
    
    def _load_courses(self):
        """Load courses data"""
        try:
            return pd.read_csv(self.data_dir / 'courses.csv')
        except Exception as e:
            logger.error(f"Error loading courses: {e}")
            return pd.DataFrame()
    
    def _load_shifts(self):
        """Load shifts data"""
        try:
            return pd.read_csv(self.data_dir / 'shifts.csv')
        except Exception as e:
            logger.error(f"Error loading shifts: {e}")
            return pd.DataFrame()
    
    def _load_shift_assignments(self):
        """Load shift assignments data"""
        try:
            df = pd.read_csv(self.data_dir / 'shift_assignments.csv')
            if not df.empty:
                df['start_date'] = pd.to_datetime(df['start_date'])
                df['end_date'] = pd.to_datetime(df['end_date'])
            return df
        except Exception as e:
            logger.error(f"Error loading shift assignments: {e}")
            return pd.DataFrame()
    
    def _load_availability(self):
        """Load availability data"""
        try:
            df = pd.read_csv(self.data_dir / 'availability.csv')
            if not df.empty:
                df['effective_date'] = pd.to_datetime(df['effective_date'])
                df['end_date'] = pd.to_datetime(df['end_date'])
            return df
        except Exception as e:
            logger.error(f"Error loading availability: {e}")
            return pd.DataFrame()
    
    def _load_time_slots(self):
        """Load time slots data"""
        try:
            df = pd.read_csv(self.data_dir / 'time_slots.csv')
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            logger.warning(f"time_slots.csv not found or empty: {e}")
            return pd.DataFrame()
    
    def get_week_schedule(self, start_date: str, tutor_ids: Optional[List[str]] = None) -> Dict:
        """
        Generate weekly grid data for specified tutors
        
        Args:
            start_date: Start date of the week (YYYY-MM-DD)
            tutor_ids: List of tutor IDs to include (None = all tutors)
        
        Returns:
            Dict with structure: {
                'tutors': [
                    {
                        'tutor_id': 'T123',
                        'tutor_name': 'John Doe',
                        'slots': {
                            '2025-11-19': {
                                '08:00': 'available',
                                '09:00': 'booked',
                                ...
                            }
                        }
                    }
                ],
                'dates': ['2025-11-19', '2025-11-20', ...],
                'hours': ['08:00', '09:00', ..., '17:00']
            }
        """
        try:
            start = pd.to_datetime(start_date)
            # Adjust to Sunday (0 = Monday, so subtract 1 day to get Sunday)
            # If start_date is Monday, go back 1 day to get Sunday
            day_of_week = start.weekday()  # 0=Monday, 6=Sunday
            if day_of_week != 6:  # If not Sunday
                days_to_subtract = (day_of_week + 1) % 7  # Convert to Sunday
                start = start - timedelta(days=days_to_subtract)
            
            # Generate dates: Sunday through Friday (6 days)
            dates = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6)]
            # Hours: 1 PM to 8 PM (13:00 to 20:00) as shown in the image
            hours = [f"{h:02d}:00" for h in range(13, 21)]  # 1 PM to 8 PM
            
            # Filter tutors if specified
            tutors_to_include = self.tutors.copy()
            if tutor_ids:
                tutors_to_include = tutors_to_include[tutors_to_include['tutor_id'].isin(tutor_ids)]
            
            schedule_data = {
                'tutors': [],
                'dates': dates,
                'hours': hours
            }
            
            for _, tutor in tutors_to_include.iterrows():
                tutor_id = tutor['tutor_id']
                tutor_name = tutor.get('full_name', f"Tutor {tutor_id}")
                
                tutor_slots = {}
                tutor_has_availability = {}  # Track if tutor has any availability per day
                
                for date_str in dates:
                    date_obj = pd.to_datetime(date_str).date()
                    day_name = date_obj.strftime('%A')
                    
                    # Check if tutor has any availability for this day
                    tutor_availability = self.availability[
                        (self.availability['tutor_id'] == tutor_id) &
                        (self.availability['day_of_week'] == day_name) &
                        (pd.to_datetime(self.availability['effective_date']).dt.date <= date_obj) &
                        (pd.to_datetime(self.availability['end_date']).dt.date >= date_obj) &
                        (self.availability['slot_status'] == 'available')
                    ]
                    
                    # Only include this day if tutor has availability
                    if not tutor_availability.empty:
                        tutor_slots[date_str] = {}
                        for hour_str in hours:
                            slot_status = self.get_slot_status(tutor_id, date_str, hour_str)
                            tutor_slots[date_str][hour_str] = slot_status
                        tutor_has_availability[date_str] = True
                    else:
                        # Tutor doesn't work on this day - don't include it
                        tutor_has_availability[date_str] = False
                
                # Only add tutor to schedule if they have availability on at least one day
                if any(tutor_has_availability.values()):
                    schedule_data['tutors'].append({
                        'tutor_id': tutor_id,
                        'tutor_name': tutor_name,
                        'slots': tutor_slots,
                        'available_days': [date for date, available in tutor_has_availability.items() if available]
                    })
            
            return schedule_data
        except Exception as e:
            logger.error(f"Error generating week schedule: {e}")
            return {'tutors': [], 'dates': [], 'hours': []}
    
    def get_available_slots(self, tutor_id: str, date: str, duration_hours: float = 1.0) -> List[Dict]:
        """
        Get all available time slots for a tutor on a date
        
        Args:
            tutor_id: Tutor ID
            date: Date (YYYY-MM-DD)
            duration_hours: Duration of appointment in hours
        
        Returns:
            List of available slots: [
                {'start_time': '09:00:00', 'end_time': '10:00:00', 'status': 'available'},
                ...
            ]
        """
        try:
            date_obj = pd.to_datetime(date).date()
            day_name = date_obj.strftime('%A')
            
            # Get tutor's availability for this day
            tutor_availability = self.availability[
                (self.availability['tutor_id'] == tutor_id) &
                (self.availability['day_of_week'] == day_name) &
                (pd.to_datetime(self.availability['effective_date']).dt.date <= date_obj) &
                (pd.to_datetime(self.availability['end_date']).dt.date >= date_obj)
            ]
            
            if tutor_availability.empty:
                return []
            
            # Get existing appointments for this tutor on this date
            existing_appointments = self.appointments[
                (self.appointments['tutor_id'] == tutor_id) &
                (pd.to_datetime(self.appointments['appointment_date']).dt.date == date_obj) &
                (self.appointments['status'].isin(['scheduled', 'completed']))
            ]
            
            available_slots = []
            
            # Generate slots based on availability windows
            for _, avail in tutor_availability.iterrows():
                start_time = pd.to_datetime(avail['start_time'], format='%H:%M:%S').time()
                end_time = pd.to_datetime(avail['end_time'], format='%H:%M:%S').time()
                
                # Generate hourly slots
                current_time = datetime.combine(date_obj, start_time)
                end_datetime = datetime.combine(date_obj, end_time)
                
                while current_time + timedelta(hours=duration_hours) <= end_datetime:
                    slot_start = current_time.time()
                    slot_end = (current_time + timedelta(hours=duration_hours)).time()
                    
                    # Check if this slot conflicts with existing appointments
                    is_available = True
                    for _, apt in existing_appointments.iterrows():
                        apt_start = apt['start_time']
                        apt_end = apt['end_time']
                        
                        # Check for overlap
                        if not (slot_end <= apt_start or slot_start >= apt_end):
                            is_available = False
                            break
                    
                    if is_available:
                        available_slots.append({
                            'start_time': slot_start.strftime('%H:%M:%S'),
                            'end_time': slot_end.strftime('%H:%M:%S'),
                            'status': 'available'
                        })
                    
                    current_time += timedelta(hours=1)
            
            return available_slots
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []
    
    def get_slot_status(self, tutor_id: str, date: str, start_time: str) -> str:
        """
        Return status of a specific slot: available/booked/unavailable
        
        Args:
            tutor_id: Tutor ID
            date: Date (YYYY-MM-DD)
            start_time: Start time (HH:MM format)
        
        Returns:
            'available', 'booked', 'unavailable', or 'pending'
        """
        try:
            date_obj = pd.to_datetime(date).date()
            time_obj = pd.to_datetime(start_time, format='%H:%M').time()
            
            # Check if tutor has availability for this day/time
            day_name = date_obj.strftime('%A')
            tutor_availability = self.availability[
                (self.availability['tutor_id'] == tutor_id) &
                (self.availability['day_of_week'] == day_name) &
                (pd.to_datetime(self.availability['effective_date']).dt.date <= date_obj) &
                (pd.to_datetime(self.availability['end_date']).dt.date >= date_obj)
            ]
            
            if tutor_availability.empty:
                return 'unavailable'
            
            # Check if time falls within any availability window
            is_in_availability = False
            for _, avail in tutor_availability.iterrows():
                avail_start = pd.to_datetime(avail['start_time'], format='%H:%M:%S').time()
                avail_end = pd.to_datetime(avail['end_time'], format='%H:%M:%S').time()
                if avail_start <= time_obj < avail_end:
                    is_in_availability = True
                    break
            
            if not is_in_availability:
                return 'unavailable'
            
            # Check for existing appointments
            existing_appointments = self.appointments[
                (self.appointments['tutor_id'] == tutor_id) &
                (pd.to_datetime(self.appointments['appointment_date']).dt.date == date_obj) &
                (self.appointments['status'].isin(['scheduled', 'completed']))
            ]
            
            for _, apt in existing_appointments.iterrows():
                apt_start = apt['start_time']
                apt_end = apt['end_time']
                
                # Check if time overlaps with appointment
                if apt_start <= time_obj < apt_end:
                    # Check confirmation status
                    if 'confirmation_status' in apt and apt.get('confirmation_status') == 'pending':
                        return 'pending'
                    return 'booked'
            
            return 'available'
        except Exception as e:
            logger.error(f"Error getting slot status: {e}")
            return 'unavailable'
    
    def book_appointment(self, tutor_id: str, student_email: str, course_id: str,
                        date: str, start_time: str, end_time: str, 
                        student_name: str = None, notes: str = '',
                        booking_type: str = 'student_booked') -> Dict:
        """
        Book a new appointment - append to appointments.csv
        
        Args:
            tutor_id: Tutor ID
            student_email: Student email
            course_id: Course ID
            date: Appointment date (YYYY-MM-DD)
            start_time: Start time (HH:MM:SS)
            end_time: End time (HH:MM:SS)
            student_name: Student name (optional)
            notes: Additional notes
            booking_type: 'student_booked' or 'admin_scheduled'
        
        Returns:
            Dict with appointment_id and success status
        """
        try:
            # Validate slot is available
            date_obj = pd.to_datetime(date).date()
            time_obj = pd.to_datetime(start_time, format='%H:%M:%S').time()
            slot_status = self.get_slot_status(tutor_id, date, time_obj.strftime('%H:%M'))
            
            if slot_status not in ['available', 'pending']:
                return {
                    'success': False,
                    'error': f'Slot is not available (status: {slot_status})'
                }
            
            # Get student name if not provided
            if not student_name:
                # Try to get from users.csv
                student_user = self.users[self.users['email'] == student_email]
                if not student_user.empty:
                    student_name = student_user.iloc[0]['full_name']
                else:
                    student_name = student_email.split('@')[0].replace('.', ' ').title()
            
            # Generate new appointment ID
            if not self.appointments.empty:
                last_id = self.appointments['appointment_id'].max()
                if pd.notna(last_id) and last_id.startswith('APT'):
                    last_num = int(last_id.replace('APT', ''))
                    new_num = last_num + 1
                else:
                    new_num = 1
            else:
                new_num = 1
            
            appointment_id = f'APT{new_num:05d}'
            
            # Prepare new appointment row
            now = datetime.now().isoformat()
            new_appointment = {
                'appointment_id': appointment_id,
                'tutor_id': tutor_id,
                'student_name': student_name,
                'student_email': student_email,
                'course_id': course_id,
                'appointment_date': date,
                'start_time': start_time,
                'end_time': end_time,
                'status': 'scheduled',
                'booking_type': booking_type,
                'confirmation_status': 'pending',
                'notes': notes,
                'created_at': now,
                'updated_at': now
            }
            
            # Append to CSV
            csv_file = self.data_dir / 'appointments.csv'
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=new_appointment.keys())
                writer.writerow(new_appointment)
            
            # Reload data to include new appointment
            self.load_data()
            
            logger.info(f"Appointment booked: {appointment_id} for {student_email}")
            
            return {
                'success': True,
                'appointment_id': appointment_id,
                'appointment': new_appointment
            }
        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_appointment(self, appointment_id: str) -> Dict:
        """
        Cancel an appointment - update status in appointments.csv
        
        Args:
            appointment_id: Appointment ID to cancel
        
        Returns:
            Dict with success status
        """
        try:
            csv_file = self.data_dir / 'appointments.csv'
            df = pd.read_csv(csv_file)
            
            # Find appointment
            appointment = df[df['appointment_id'] == appointment_id]
            if appointment.empty:
                return {
                    'success': False,
                    'error': 'Appointment not found'
                }
            
            # Update status
            df.loc[df['appointment_id'] == appointment_id, 'status'] = 'cancelled'
            df.loc[df['appointment_id'] == appointment_id, 'confirmation_status'] = 'cancelled'
            df.loc[df['appointment_id'] == appointment_id, 'updated_at'] = datetime.now().isoformat()
            
            # Save back to CSV
            df.to_csv(csv_file, index=False)
            
            # Reload data
            self.load_data()
            
            logger.info(f"Appointment cancelled: {appointment_id}")
            
            return {
                'success': True,
                'appointment_id': appointment_id
            }
        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_my_appointments(self, student_email: str, upcoming_only: bool = True) -> List[Dict]:
        """
        Get appointments for a specific student
        
        Args:
            student_email: Student email
            upcoming_only: If True, only return future appointments
        
        Returns:
            List of appointment dictionaries
        """
        try:
            appointments = self.appointments[
                self.appointments['student_email'] == student_email
            ].copy()
            
            if upcoming_only:
                today = datetime.now().date()
                appointments = appointments[
                    pd.to_datetime(appointments['appointment_date']).dt.date >= today
                ]
            
            # Convert to list of dicts
            result = appointments.to_dict('records')
            
            # Convert datetime objects to strings for JSON serialization
            for apt in result:
                if 'appointment_date' in apt and pd.notna(apt['appointment_date']):
                    apt['appointment_date'] = str(apt['appointment_date'])
                if 'start_time' in apt and isinstance(apt['start_time'], time):
                    apt['start_time'] = apt['start_time'].strftime('%H:%M:%S')
                if 'end_time' in apt and isinstance(apt['end_time'], time):
                    apt['end_time'] = apt['end_time'].strftime('%H:%M:%S')
            
            return result
        except Exception as e:
            logger.error(f"Error getting student appointments: {e}")
            return []

