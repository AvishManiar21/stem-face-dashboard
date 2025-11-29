"""
Core Analytics Module for Scheduling System
Provides analytics based on appointments, shifts, and schedules
No check-in/check-out - purely scheduling based
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulingAnalytics:
    """Analytics for appointment and scheduling system"""
    
    def __init__(self, data_dir='data/core', max_date=None):
        self.data_dir = Path(data_dir)
        self.max_date = max_date or pd.Timestamp.now().normalize()
        self.load_all_data()
    
    def load_all_data(self):
        """Load all core CSV files"""
        try:
            self.users = pd.read_csv(self.data_dir / 'users.csv')
            self.tutors = pd.read_csv(self.data_dir / 'tutors.csv')
            self.courses = pd.read_csv(self.data_dir / 'courses.csv')
            self.appointments = pd.read_csv(self.data_dir / 'appointments.csv')
            self.shifts = pd.read_csv(self.data_dir / 'shifts.csv')
            self.shift_assignments = pd.read_csv(self.data_dir / 'shift_assignments.csv')
            self.availability = pd.read_csv(self.data_dir / 'availability.csv')
            self.tutor_courses = pd.read_csv(self.data_dir / 'tutor_courses.csv')
            
            # Convert date columns
            if not self.appointments.empty:
                self.appointments['appointment_date'] = pd.to_datetime(self.appointments['appointment_date'])
                self.appointments['created_at'] = pd.to_datetime(self.appointments['created_at'])
            
            if not self.shift_assignments.empty:
                self.shift_assignments['start_date'] = pd.to_datetime(self.shift_assignments['start_date'])
                self.shift_assignments['end_date'] = pd.to_datetime(self.shift_assignments['end_date'])
            
            logger.info(f"Loaded data: {len(self.appointments)} appointments, {len(self.tutors)} tutors")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            # Initialize empty dataframes
            self.users = pd.DataFrame()
            self.tutors = pd.DataFrame()
            self.courses = pd.DataFrame()
            self.appointments = pd.DataFrame()
            self.shifts = pd.DataFrame()
            self.shift_assignments = pd.DataFrame()
            self.availability = pd.DataFrame()
            self.tutor_courses = pd.DataFrame()
    
    def apply_filters(self, tutor_ids=None, start_date=None, end_date=None, status=None, course_ids=None):
        """Apply filters to appointments data"""
        df = self.appointments.copy()
        
        if df.empty:
            return df
        
        # Filter by date range
        if start_date:
            df = df[df['appointment_date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['appointment_date'] <= pd.to_datetime(end_date)]
        
        # Filter by max_date
        df = df[df['appointment_date'] <= self.max_date]
        
        # Filter by tutors
        if tutor_ids:
            if isinstance(tutor_ids, str):
                tutor_ids = [t.strip() for t in tutor_ids.split(',') if t.strip()]
            df = df[df['tutor_id'].isin(tutor_ids)]
        
        # Filter by status
        if status and status != 'all':
            df = df[df['status'] == status]
        
        # Filter by courses
        if course_ids:
            if isinstance(course_ids, str):
                course_ids = [c.strip() for c in course_ids.split(',') if c.strip()]
            df = df[df['course_id'].isin(course_ids)]
        
        return df
    
    def get_tutor_name(self, tutor_id):
        """Get tutor name from user data"""
        tutor = self.tutors[self.tutors['tutor_id'] == tutor_id]
        if tutor.empty:
            return str(tutor_id)
        user_id = tutor.iloc[0]['user_id']
        user = self.users[self.users['user_id'] == user_id]
        if user.empty:
            return str(tutor_id)
        return user.iloc[0]['full_name']
    
    def get_course_name(self, course_id):
        """Get course name"""
        course = self.courses[self.courses['course_id'] == course_id]
        if course.empty:
            return str(course_id)
        return course.iloc[0]['course_name']
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to native Python types"""
        if isinstance(obj, dict):
            return {self._convert_numpy_types(key): self._convert_numpy_types(value) 
                   for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif pd.isna(obj):
            return None
        return obj
    
    def get_chart_data(self, dataset, **filters):
        """Get chart data based on dataset type"""
        df = self.apply_filters(**filters)
        
        if df.empty and dataset not in ['shifts_overview', 'tutor_availability']:
            return {}
        
        # Map dataset names to methods
        dataset_methods = {
            'appointments_per_tutor': self.appointments_per_tutor,
            'hours_per_tutor': self.hours_per_tutor,
            'daily_appointments': self.daily_appointments,
            'daily_hours': self.daily_hours,
            'appointments_by_status': self.appointments_by_status,
            'appointments_by_course': self.appointments_by_course,
            'appointments_per_day_of_week': self.appointments_per_day_of_week,
            'avg_hours_per_day_of_week': self.avg_hours_per_day_of_week,
            'monthly_appointments': self.monthly_appointments,
            'monthly_hours': self.monthly_hours,
            'cumulative_appointments': self.cumulative_appointments,
            'cumulative_hours': self.cumulative_hours,
            'hourly_distribution': self.hourly_distribution,
            'appointment_duration_distribution': self.appointment_duration_distribution,
            'tutor_course_distribution': self.tutor_course_distribution,
            'shifts_overview': self.shifts_overview,
            'tutor_availability': self.tutor_availability,
        }
        
        method = dataset_methods.get(dataset)
        if method:
            result = method(df)
            return self._convert_numpy_types(result)
        
        return {}
    
    def appointments_per_tutor(self, df):
        """Count appointments per tutor"""
        if df.empty:
            return {}
        counts = df.groupby('tutor_id').size()
        result = {}
        for tutor_id, count in counts.items():
            tutor_name = self.get_tutor_name(tutor_id)
            result[tutor_name] = int(count)
        return result
    
    def hours_per_tutor(self, df):
        """Calculate scheduled hours per tutor"""
        if df.empty:
            return {}
        
        # Calculate duration in hours
        df['duration_hours'] = df.apply(lambda row: self._calculate_duration(
            row['start_time'], row['end_time']), axis=1)
        
        hours = df.groupby('tutor_id')['duration_hours'].sum()
        result = {}
        for tutor_id, total_hours in hours.items():
            tutor_name = self.get_tutor_name(tutor_id)
            result[tutor_name] = float(round(total_hours, 2))
        return result
    
    def _calculate_duration(self, start_time, end_time):
        """Calculate duration between two times in hours"""
        try:
            if pd.isna(start_time) or pd.isna(end_time):
                return 0
            start = pd.to_datetime(start_time, format='%H:%M:%S')
            end = pd.to_datetime(end_time, format='%H:%M:%S')
            duration = (end - start).total_seconds() / 3600
            return max(0, duration)
        except:
            return 0
    
    def daily_appointments(self, df):
        """Count appointments per day"""
        if df.empty:
            return {}
        daily = df.groupby(df['appointment_date'].dt.date).size()
        return {str(date): int(count) for date, count in daily.items()}
    
    def daily_hours(self, df):
        """Calculate scheduled hours per day"""
        if df.empty:
            return {}
        df['duration_hours'] = df.apply(lambda row: self._calculate_duration(
            row['start_time'], row['end_time']), axis=1)
        daily = df.groupby(df['appointment_date'].dt.date)['duration_hours'].sum()
        return {str(date): float(round(hours, 2)) for date, hours in daily.items()}
    
    def appointments_by_status(self, df):
        """Count appointments by status"""
        if df.empty:
            return {}
        status_counts = df['status'].value_counts()
        return {status: int(count) for status, count in status_counts.items()}
    
    def appointments_by_course(self, df):
        """Count appointments by course"""
        if df.empty:
            return {}
        course_counts = df.groupby('course_id').size()
        result = {}
        for course_id, count in course_counts.items():
            course_name = self.get_course_name(course_id)
            result[course_name] = int(count)
        return result
    
    def appointments_per_day_of_week(self, df):
        """Count appointments per day of week"""
        if df.empty:
            return {}
        df['day_of_week'] = df['appointment_date'].dt.day_name()
        day_counts = df['day_of_week'].value_counts()
        
        # Ensure all days are present
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        result = {day: int(day_counts.get(day, 0)) for day in days_order}
        return result
    
    def avg_hours_per_day_of_week(self, df):
        """Average hours per day of week"""
        if df.empty:
            return {}
        df['day_of_week'] = df['appointment_date'].dt.day_name()
        df['duration_hours'] = df.apply(lambda row: self._calculate_duration(
            row['start_time'], row['end_time']), axis=1)
        
        # Group by day and calculate mean
        day_hours = df.groupby('day_of_week')['duration_hours'].mean()
        
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        result = {day: float(round(day_hours.get(day, 0), 2)) for day in days_order}
        return result
    
    def monthly_appointments(self, df):
        """Count appointments per month"""
        if df.empty:
            return {}
        df['year_month'] = df['appointment_date'].dt.to_period('M')
        monthly = df.groupby('year_month').size()
        return {str(month): int(count) for month, count in monthly.items()}
    
    def monthly_hours(self, df):
        """Calculate hours per month"""
        if df.empty:
            return {}
        df['year_month'] = df['appointment_date'].dt.to_period('M')
        df['duration_hours'] = df.apply(lambda row: self._calculate_duration(
            row['start_time'], row['end_time']), axis=1)
        monthly = df.groupby('year_month')['duration_hours'].sum()
        return {str(month): float(round(hours, 2)) for month, hours in monthly.items()}
    
    def cumulative_appointments(self, df):
        """Cumulative appointments over time"""
        if df.empty:
            return {}
        df_sorted = df.sort_values('appointment_date')
        df_sorted['cumulative'] = range(1, len(df_sorted) + 1)
        daily_cum = df_sorted.groupby(df_sorted['appointment_date'].dt.date)['cumulative'].last()
        return {str(date): int(count) for date, count in daily_cum.items()}
    
    def cumulative_hours(self, df):
        """Cumulative hours over time"""
        if df.empty:
            return {}
        df['duration_hours'] = df.apply(lambda row: self._calculate_duration(
            row['start_time'], row['end_time']), axis=1)
        df_sorted = df.sort_values('appointment_date')
        df_sorted['cumulative_hours'] = df_sorted['duration_hours'].cumsum()
        daily_cum = df_sorted.groupby(df_sorted['appointment_date'].dt.date)['cumulative_hours'].last()
        return {str(date): float(round(hours, 2)) for date, hours in daily_cum.items()}
    
    def hourly_distribution(self, df):
        """Distribution of appointments by hour of day"""
        if df.empty:
            return {}
        
        df['hour'] = df['start_time'].apply(lambda x: int(str(x).split(':')[0]) if pd.notna(x) else None)
        df = df[df['hour'].notna()]
        hour_counts = df['hour'].value_counts()
        
        # Create result for all hours
        result = {f"{h:02d}:00": int(hour_counts.get(h, 0)) for h in range(24)}
        return result
    
    def appointment_duration_distribution(self, df):
        """Distribution of appointment durations"""
        if df.empty:
            return {}
        
        df['duration_hours'] = df.apply(lambda row: self._calculate_duration(
            row['start_time'], row['end_time']), axis=1)
        
        # Categorize durations
        bins = [0, 0.5, 1, 1.5, 2, 3, 24]
        labels = ['<30min', '30min-1h', '1h-1.5h', '1.5h-2h', '2h-3h', '3h+']
        df['duration_category'] = pd.cut(df['duration_hours'], bins=bins, labels=labels, include_lowest=True)
        
        duration_counts = df['duration_category'].value_counts()
        return {str(cat): int(count) for cat, count in duration_counts.items()}
    
    def tutor_course_distribution(self, df):
        """Show which courses each tutor teaches"""
        if self.tutor_courses.empty:
            return {}
        
        # Get tutor-course mappings
        result = {}
        for _, row in self.tutor_courses.iterrows():
            tutor_name = self.get_tutor_name(row['tutor_id'])
            course_name = self.get_course_name(row['course_id'])
            if tutor_name not in result:
                result[tutor_name] = []
            result[tutor_name].append(course_name)
        
        # Convert to count format
        return {tutor: len(courses) for tutor, courses in result.items()}
    
    def shifts_overview(self, df):
        """Overview of scheduled shifts"""
        if self.shift_assignments.empty:
            return {}
        
        # Count active assignments per tutor
        active = self.shift_assignments[self.shift_assignments['active'] == 'True']
        shift_counts = active.groupby('tutor_name').size()
        return {tutor: int(count) for tutor, count in shift_counts.items()}
    
    def tutor_availability(self, df):
        """Show tutor availability windows"""
        if self.availability.empty:
            return {}
        
        # Count availability windows per tutor
        avail_counts = self.availability.groupby('tutor_id').size()
        result = {}
        for tutor_id, count in avail_counts.items():
            tutor_name = self.get_tutor_name(tutor_id)
            result[tutor_name] = int(count)
        return result
    
    def get_summary_stats(self, **filters):
        """Get summary statistics"""
        df = self.apply_filters(**filters)
        
        if df.empty:
            return {
                'total_appointments': 0,
                'total_hours': 0,
                'active_tutors': 0,
                'avg_duration': 0
            }
        
        df['duration_hours'] = df.apply(lambda row: self._calculate_duration(
            row['start_time'], row['end_time']), axis=1)
        
        return {
            'total_appointments': len(df),
            'total_hours': float(round(df['duration_hours'].sum(), 2)),
            'active_tutors': df['tutor_id'].nunique(),
            'avg_duration': float(round(df['duration_hours'].mean(), 2))
        }

