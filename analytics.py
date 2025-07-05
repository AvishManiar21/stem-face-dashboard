#!/usr/bin/env python3
"""
Analytics module for tutor dashboard
Handles alerts and calendar functionality
"""

import pandas as pd
import numpy as np
from datetime import datetime as dt, timedelta, date
import calendar
from collections import defaultdict
import os
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)

# Optional email imports
EMAIL_AVAILABLE = False

# Create dummy classes to prevent NameError
class _DummyMIMEText:
    def __init__(self, *args, **kwargs):
        pass

class _DummyMIMEMultipart:
    def __init__(self, *args, **kwargs):
        pass
    
    def __setitem__(self, key, value):
        pass
    
    def attach(self, payload):
        pass
    
    def as_string(self):
        return ""

class _DummySMTP:
    def __init__(self, *args, **kwargs):
        pass
    
    def starttls(self):
        pass
    
    def login(self, *args):
        pass
    
    def send_message(self, *args):
        pass
    
    def sendmail(self, *args):
        pass
    
    def quit(self):
        pass

# Set defaults to dummy classes
class _DummySMTPLib:
    SMTP = _DummySMTP

smtplib = _DummySMTPLib()
MIMEText = _DummyMIMEText
MIMEMultipart = _DummyMIMEMultipart

try:
    import smtplib
    from email.mime.text import MIMEText as _RealMIMEText
    from email.mime.multipart import MIMEMultipart as _RealMIMEMultipart
    MIMEText = _RealMIMEText  # type: ignore
    MIMEMultipart = _RealMIMEMultipart  # type: ignore
    EMAIL_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Email functionality not available: {e}")
    EMAIL_AVAILABLE = False

class TutorAnalytics:
    """
    Analytics for tutor face recognition data.
    All KPIs and analytics are computed up to 'max_date' (default: today).
    """
    def __init__(self, face_log_file='logs/face_log_with_expected.csv', max_date=None):
        self.face_log_file = face_log_file
        self.max_date = max_date or pd.Timestamp.now().normalize()
        self.data = self.load_data()
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to native Python types for JSON serialization"""
        if isinstance(obj, dict):
            # Convert both keys and values
            return {self._convert_numpy_types(key): self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.str_):
            return str(obj)
        elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
            return str(obj)
        elif pd.isna(obj):
            return None
        elif hasattr(obj, 'item'):  # For numpy scalars
            try:
                return obj.item()
            except (ValueError, AttributeError):
                return str(obj)
        elif hasattr(obj, 'dtype'):  # Any other numpy/pandas type
            try:
                return obj.item() if hasattr(obj, 'item') else str(obj)
            except (ValueError, AttributeError):
                return str(obj)
        else:
            return obj
    
    def _safe_float_convert(self, value, default=0.0):
        """Safely convert a value to float, handling complex numbers and other edge cases"""
        try:
            if pd.isna(value):
                return default
            if isinstance(value, (complex, np.complexfloating)):
                return float(value.real)
            if isinstance(value, (int, float, np.integer, np.floating)):
                return float(value)
            if isinstance(value, str):
                return float(value)
            return float(value)
        except (ValueError, TypeError, AttributeError):
            return default
    
    def load_data(self):
        """Load and preprocess face log data"""
        try:
            df = pd.read_csv(self.face_log_file)
            if df.empty:
                return pd.DataFrame()
            
            # Parse datetime columns
            df['check_in'] = pd.to_datetime(df['check_in'], format='mixed', errors='coerce')
            df['check_out'] = pd.to_datetime(df['check_out'], format='mixed', errors='coerce')
            
            # Filter to max_date if set
            if self.max_date is not None:
                df = df[df['check_in'].dt.date <= self.max_date.date()]
            
            # Add derived columns
            df['date'] = df['check_in'].dt.date
            # Ensure 'date' is always a datetime.date object
            df['date'] = df['date'].apply(lambda d: d if isinstance(d, date) else pd.to_datetime(d).date() if pd.notna(d) else None)
            # Remove or comment out debug print of unique dates
            # print(f"[DEBUG] Unique dates after loading: {sorted(df['date'].unique())}")
            df['day_of_week'] = df['check_in'].dt.day_name()
            df['hour'] = df['check_in'].dt.hour
            df['week'] = df['check_in'].dt.isocalendar().week
            df['month'] = df['check_in'].dt.month
            
            return df.sort_values('check_in')
        except FileNotFoundError:
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    # ==================== CALENDAR VIEW ====================
    
    def get_session_status(self, session):
        """Determine the status of a session"""
        if pd.isna(session['check_out']):
            return 'missing_checkout'
        elif session['shift_hours'] < 1.0:
            return 'short_shift'
        elif session['shift_hours'] >= 6.0:
            return 'long_shift'
        else:
            return 'normal'
    
    def get_day_status(self, day_data):
        """Determine the overall status of a day"""
        if day_data.empty:
            return 'inactive'
        
        total_hours = day_data['shift_hours'].sum()
        has_issues = day_data['check_out'].isna().any() or (day_data['shift_hours'] < 1.0).any()
        
        if has_issues:
            return 'warning'
        elif total_hours >= 10:
            return 'high_activity'
        elif total_hours >= 5:
            return 'normal'
        else:
            return 'low_activity'
    
    def day_has_issues(self, day_data):
        """Check if a day has any issues that need attention"""
        if day_data.empty:
            return False
        
        # Check for missing checkouts
        missing_checkouts = day_data['check_out'].isna().any()
        
        # Check for very short sessions
        short_sessions = (day_data['shift_hours'] < 0.5).any()
        
        # Check for very long sessions
        long_sessions = (day_data['shift_hours'] > 12).any()
        
        return missing_checkouts or short_sessions or long_sessions

    def get_audit_logs(self, page=1, per_page=20):
        """Get paginated audit logs for admin view"""
        try:
            # Load audit logs from CSV
            audit_file = 'logs/audit_log.csv'
            if not os.path.exists(audit_file):
                # Create sample audit logs if file doesn't exist
                self._create_sample_audit_logs()
            df = pd.read_csv(audit_file)
            print(f"[DEBUG] audit_log.csv columns: {df.columns.tolist()}")
            
            # Map existing columns to expected format
            # Your audit log has: timestamp, user_email, action, details, ip_address, user_agent
            # Frontend expects: timestamp, user_email, action, details, ip_address, user_agent, user_name, admin_email, etc.
            
            # Add missing columns for frontend compatibility
            if 'user_name' not in df.columns:
                # Handle empty user_email values safely
                df['user_name'] = ''
                if 'user_email' in df.columns:
                    df['user_email'] = df['user_email'].astype(str)
                    mask = df['user_email'].notna() & (df['user_email'] != '') & (df['user_email'] != 'nan')
                    df.loc[mask, 'user_name'] = df.loc[mask, 'user_email'].str.split('@').str[0]
            if 'admin_email' not in df.columns:
                df['admin_email'] = df['user_email'] if 'user_email' in df.columns else ''
            if 'admin_user_id' not in df.columns:
                df['admin_user_id'] = ''
            if 'target_user_email' not in df.columns:
                df['target_user_email'] = ''
            if 'status' not in df.columns:
                df['status'] = 'completed'
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.sort_values('timestamp', ascending=False)
            
            total = len(df)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_df = df.iloc[start_idx:end_idx]
            
            # Convert timestamps to ISO strings for JSON serialization
            paginated_df = paginated_df.copy()  # Create a copy to avoid SettingWithCopyWarning
            paginated_df['timestamp'] = paginated_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            # Replace NaN with None for JSON serialization
            paginated_df = paginated_df.where(pd.notnull(paginated_df), None)
            logs = paginated_df.to_dict('records')
            return {'logs': logs, 'total': total}
        except Exception as e:
            import traceback
            print(f"Error loading audit logs: {e}")
            traceback.print_exc()
            return {'logs': [], 'total': 0}

    def _create_sample_audit_logs(self):
        """Create sample audit logs for testing"""
        import random
        from datetime import datetime, timedelta
        
        audit_data = []
        actions = ['login', 'logout', 'check_in', 'check_out', 'manual_entry', 'data_export']
        users = ['admin@example.com', 'manager@example.com', 'tutor1@example.com', 'tutor2@example.com']
        
        # Generate 100 sample audit entries
        for i in range(100):
            timestamp = datetime.now() - timedelta(days=random.randint(0, 30), 
                                                 hours=random.randint(0, 23),
                                                 minutes=random.randint(0, 59))
            
            action = random.choice(actions)
            user = random.choice(users)
            
            audit_data.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'user_email': user,
                'action': action,
                'details': f'Sample {action} action',
                'ip_address': f'192.168.1.{random.randint(1, 255)}',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        
        # Create directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Save to CSV
        df = pd.DataFrame(audit_data)
        df.to_csv('logs/audit_log.csv', index=False)

    def populate_audit_logs(self):
        """Populate audit logs with current data"""
        self._create_sample_audit_logs()

    def get_shifts_data(self):
        """Get shifts data for admin management"""
        try:
            # Load shifts from CSV
            shifts_file = 'logs/shifts.csv'
            if not os.path.exists(shifts_file):
                # Create sample shifts if file doesn't exist
                self._create_sample_shifts()
            
            df_shifts = pd.read_csv(shifts_file)
            
            # Load assignments
            assignments_file = 'logs/shift_assignments.csv'
            if not os.path.exists(assignments_file):
                self._create_sample_assignments()
            
            df_assignments = pd.read_csv(assignments_file)
            
            return {
                'shifts': df_shifts.to_dict('records'),
                'assignments': df_assignments.to_dict('records'),
                'tutors': self._get_available_tutors()
            }
            
        except Exception as e:
            print(f"Error loading shifts data: {e}")
            return {'shifts': [], 'assignments': [], 'tutors': []}

    def _create_sample_shifts(self):
        """Create sample shifts for testing"""
        shifts_data = [
            {
                'shift_id': 1,
                'shift_name': 'Morning Shift',
                'start_time': '08:00',
                'end_time': '12:00',
                'days_of_week': 'Monday,Tuesday,Wednesday,Thursday,Friday',
                'status': 'active'
            },
            {
                'shift_id': 2,
                'shift_name': 'Afternoon Shift',
                'start_time': '12:00',
                'end_time': '16:00',
                'days_of_week': 'Monday,Tuesday,Wednesday,Thursday,Friday',
                'status': 'active'
            },
            {
                'shift_id': 3,
                'shift_name': 'Evening Shift',
                'start_time': '16:00',
                'end_time': '20:00',
                'days_of_week': 'Monday,Tuesday,Wednesday,Thursday,Friday',
                'status': 'active'
            },
            {
                'shift_id': 4,
                'shift_name': 'Weekend Shift',
                'start_time': '10:00',
                'end_time': '18:00',
                'days_of_week': 'Saturday,Sunday',
                'status': 'active'
            }
        ]
        
        os.makedirs('logs', exist_ok=True)
        df = pd.DataFrame(shifts_data)
        df.to_csv('logs/shifts.csv', index=False)

    def _create_sample_assignments(self):
        """Create sample shift assignments for testing"""
        assignments_data = [
            {
                'assignment_id': 1,
                'shift_id': 1,
                'tutor_id': 'T001',
                'tutor_name': 'John Doe',
                'assigned_date': '2024-01-01',
                'status': 'active'
            },
            {
                'assignment_id': 2,
                'shift_id': 2,
                'tutor_id': 'T002',
                'tutor_name': 'Jane Smith',
                'assigned_date': '2024-01-01',
                'status': 'active'
            },
            {
                'assignment_id': 3,
                'shift_id': 3,
                'tutor_id': 'T003',
                'tutor_name': 'Bob Johnson',
                'assigned_date': '2024-01-01',
                'status': 'active'
            }
        ]
        
        os.makedirs('logs', exist_ok=True)
        df = pd.DataFrame(assignments_data)
        df.to_csv('logs/shift_assignments.csv', index=False)

    def _get_available_tutors(self):
        """Get list of available tutors"""
        try:
            df = self.load_data()
            if df.empty:
                return []
            
            tutors = df[['tutor_id', 'tutor_name']].drop_duplicates()
            return tutors.to_dict('records')
        except:
            return []

    def remove_shift_assignment(self, assignment_id):
        """Remove a shift assignment"""
        try:
            assignments_file = 'logs/shift_assignments.csv'
            if os.path.exists(assignments_file):
                df = pd.read_csv(assignments_file)
                df = df[df['assignment_id'] != int(assignment_id)]
                df.to_csv(assignments_file, index=False)
        except Exception as e:
            print(f"Error removing assignment: {e}")

    def deactivate_shift(self, shift_id):
        """Deactivate a shift"""
        try:
            shifts_file = 'logs/shifts.csv'
            if os.path.exists(shifts_file):
                df = pd.read_csv(shifts_file)
                df.loc[df['shift_id'] == int(shift_id), 'status'] = 'inactive'
                df.to_csv(shifts_file, index=False)
        except Exception as e:
            print(f"Error deactivating shift: {e}")

    def create_shift(self, shift_name, start_time, end_time, days_of_week):
        """Create a new shift"""
        try:
            shifts_file = 'logs/shifts.csv'
            if os.path.exists(shifts_file):
                df = pd.read_csv(shifts_file)
                new_shift_id = df['shift_id'].max() + 1 if len(df) > 0 else 1
            else:
                df = pd.DataFrame(columns=['shift_id', 'shift_name', 'start_time', 'end_time', 'days_of_week', 'status'])
                new_shift_id = 1
            
            new_shift = {
                'shift_id': new_shift_id,
                'shift_name': shift_name,
                'start_time': start_time,
                'end_time': end_time,
                'days_of_week': ','.join(days_of_week),
                'status': 'active'
            }
            
            df = pd.concat([df, pd.DataFrame([new_shift])], ignore_index=True)
            df.to_csv(shifts_file, index=False)
            
        except Exception as e:
            print(f"Error creating shift: {e}")

    def assign_shift_to_tutor(self, shift_id, tutor_id):
        """Assign a shift to a tutor"""
        try:
            assignments_file = 'logs/shift_assignments.csv'
            if os.path.exists(assignments_file):
                df = pd.read_csv(assignments_file)
                new_assignment_id = df['assignment_id'].max() + 1 if len(df) > 0 else 1
            else:
                df = pd.DataFrame(columns=['assignment_id', 'shift_id', 'tutor_id', 'tutor_name', 'assigned_date', 'status'])
                new_assignment_id = 1
            
            # Get tutor name from face log
            tutor_name = f"Tutor {tutor_id}"
            try:
                face_df = pd.read_csv('logs/face_log.csv')
                tutor_row = face_df[face_df['tutor_id'] == tutor_id]
                if not tutor_row.empty:
                    tutor_name = tutor_row['tutor_name'].iloc[0]
            except:
                pass
            
            new_assignment = {
                'assignment_id': new_assignment_id,
                'shift_id': int(shift_id),
                'tutor_id': tutor_id,
                'tutor_name': tutor_name,
                'assigned_date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'active'
            }
            
            df = pd.concat([df, pd.DataFrame([new_assignment])], ignore_index=True)
            df.to_csv(assignments_file, index=False)
            
        except Exception as e:
            print(f"Error assigning shift: {e}")

    def get_logs_for_collapsible_view(self):
        """
        Return all check-in/check-out logs as a list of dicts for the dashboard's collapsible log view.
        """
        if self.data.empty:
            return []
        logs = []
        for _, row in self.data.iterrows():
            logs.append({
                'tutor_id': row.get('tutor_id'),
                'tutor_name': row.get('tutor_name'),
                'check_in': row.get('check_in').strftime('%Y-%m-%d %H:%M') if not pd.isna(row.get('check_in')) else None,
                'check_out': row.get('check_out').strftime('%Y-%m-%d %H:%M') if not pd.isna(row.get('check_out')) else None,
                'shift_hours': float(row.get('shift_hours')) if not pd.isna(row.get('shift_hours')) else None,
                'snapshot_in': row.get('snapshot_in'),
                'snapshot_out': row.get('snapshot_out')
            })
        return logs

    def get_dashboard_summary(self):
        """
        Return a summary of KPIs for the dashboard, deduplicating logic from other methods.
        """
        if self.data.empty:
            return {
                'total_checkins': 0,
                'total_hours': 0,
                'active_tutors': 0,
                'avg_session_duration': '—',
                'avg_daily_hours': '—',
                'peak_checkin_hour': '—',
                'top_day': '—',
                'top_tutor_current_month': '—',
            }
        df = self.data.copy()
        # Remove duplicate check-ins by tutor_id and check_in time
        df = df.drop_duplicates(subset=['tutor_id', 'check_in'])
        total_checkins = len(df)
        total_hours = round(df['shift_hours'].sum(), 1)
        active_tutors = df['tutor_id'].nunique()
        avg_session_duration = round(df['shift_hours'].mean(), 2) if total_checkins > 0 else '—'
        # Daily hours
        daily_hours = df.groupby('date')['shift_hours'].sum()
        avg_daily_hours = round(daily_hours.mean(), 2) if not daily_hours.empty else '—'
        # Peak check-in hour
        if 'hour' in df.columns and not df['hour'].isna().all():
            peak_checkin_hour = int(df['hour'].mode()[0])
        else:
            peak_checkin_hour = '—'
        # Most active day
        if not daily_hours.empty:
            top_day = str(daily_hours.idxmax())
        else:
            top_day = '—'
        # Top tutor this month
        now = pd.Timestamp.now()
        month_df = df[(df['check_in'].dt.month == now.month) & (df['check_in'].dt.year == now.year)]
        if not month_df.empty:
            top_tutor_row = month_df.groupby(['tutor_id', 'tutor_name'])['shift_hours'].sum().idxmax()
            top_tutor_current_month = top_tutor_row[1] if isinstance(top_tutor_row, tuple) and len(top_tutor_row) > 1 else str(top_tutor_row)
        else:
            top_tutor_current_month = '—'
        return {
            'total_checkins': total_checkins,
            'total_hours': total_hours,
            'active_tutors': active_tutors,
            'avg_session_duration': avg_session_duration,
            'avg_daily_hours': avg_daily_hours,
            'peak_checkin_hour': peak_checkin_hour,
            'top_day': top_day,
            'top_tutor_current_month': top_tutor_current_month,
        }

    def generate_alerts(self):
        """
        Generate alerts for the dashboard based on data analysis.
        """
        alerts = []
        
        if self.data.empty:
            return alerts
        
        # Check for missing checkouts
        missing_checkouts = self.data[self.data['check_out'].isna()]
        if len(missing_checkouts) > 0:
            alerts.append({
                'type': 'warning',
                'title': 'Missing Check-outs',
                'message': f'{len(missing_checkouts)} sessions have missing check-out times'
            })
        
        # Check for very short sessions (less than 30 minutes)
        short_sessions = self.data[self.data['shift_hours'] < 0.5]
        if len(short_sessions) > 0:
            alerts.append({
                'type': 'info',
                'title': 'Short Sessions',
                'message': f'{len(short_sessions)} sessions are shorter than 30 minutes'
            })
        
        # Check for very long sessions (more than 8 hours)
        long_sessions = self.data[self.data['shift_hours'] > 8]
        if len(long_sessions) > 0:
            alerts.append({
                'type': 'warning',
                'title': 'Long Sessions',
                'message': f'{len(long_sessions)} sessions are longer than 8 hours'
            })
        
        # Check for low activity days
        daily_activity = self.data.groupby('date').size()
        low_activity_days = daily_activity[daily_activity < 3]
        if len(low_activity_days) > 0:
            alerts.append({
                'type': 'info',
                'title': 'Low Activity Days',
                'message': f'{len(low_activity_days)} days have fewer than 3 check-ins'
            })
        
        # Check for inactive tutors (no check-ins in last 7 days)
        if not self.data.empty:
            last_week = pd.Timestamp.now() - pd.Timedelta(days=7)
            recent_activity = self.data[self.data['check_in'] >= last_week]
            active_tutors = recent_activity['tutor_id'].nunique()
            total_tutors = self.data['tutor_id'].nunique()
            
            if active_tutors < total_tutors * 0.7:  # Less than 70% active
                alerts.append({
                    'type': 'warning',
                    'title': 'Low Tutor Activity',
                    'message': f'Only {active_tutors} out of {total_tutors} tutors active in the last week'
                })
        
        return alerts

    def get_session_duration_vs_checkin_hour(self):
        if self.data.empty:
            return []
        # Only include rows with valid check_in and shift_hours
        df = self.data.dropna(subset=['check_in', 'shift_hours'])
        result = []
        for _, row in df.iterrows():
            try:
                checkin_hour = pd.to_datetime(row['check_in']).hour
                duration = float(row['shift_hours'])
                result.append({'x': checkin_hour, 'y': duration})
            except Exception:
                continue
        return result

    def get_chart_data(self, dataset):
        """
        Get chart data based on the dataset type.
        """
        if self.data.empty:
            return {}
        
        try:
            if dataset == 'checkins_per_tutor':
                return self.data.groupby('tutor_name').size().to_dict()
            elif dataset == 'hours_per_tutor':
                return self.data.groupby('tutor_name')['shift_hours'].sum().to_dict()
            elif dataset == 'daily_checkins':
                # Convert date objects to strings for JSON serialization
                daily_data = self.data.groupby('date').size()
                return {str(date): int(count) for date, count in daily_data.items()}
            elif dataset == 'daily_hours':
                # Convert date objects to strings for JSON serialization
                daily_data = self.data.groupby('date')['shift_hours'].sum()
                return {str(date): float(count) for date, count in daily_data.items()}
            elif dataset == 'hourly_checkins_dist':
                # Convert hour integers to strings for JSON serialization
                hourly_data = self.data.groupby('hour').size()
                return {str(hour): int(count) for hour, count in hourly_data.items()}
            elif dataset == 'monthly_hours':
                # Convert month integers to strings for JSON serialization
                monthly_data = self.data.groupby('month')['shift_hours'].sum()
                return {str(month): float(hours) for month, hours in monthly_data.items()}
            elif dataset == 'avg_hours_per_day_of_week':
                # Convert day names to strings for JSON serialization
                daily_avg = self.data.groupby('day_of_week')['shift_hours'].mean()
                return {str(day): float(avg) for day, avg in daily_avg.items()}
            elif dataset == 'checkins_per_day_of_week':
                # Convert day names to strings for JSON serialization
                daily_counts = self.data.groupby('day_of_week').size()
                return {str(day): int(count) for day, count in daily_counts.items()}
            elif dataset == 'hourly_activity_by_day':
                # Create hourly activity heatmap data
                hourly_by_day = self.data.groupby(['day_of_week', 'hour']).size().unstack(fill_value=0)
                return {str(day): {str(hour): int(count) for hour, count in day_data.items()} 
                       for day, day_data in hourly_by_day.items()}
            elif dataset == 'session_duration_distribution':
                # Create session duration distribution
                duration_ranges = pd.cut(self.data['shift_hours'], 
                                       bins=[0, 1, 2, 4, 6, 8, float('inf')], 
                                       labels=['0-1h', '1-2h', '2-4h', '4-6h', '6-8h', '8h+'])
                duration_counts = duration_ranges.value_counts()
                return {str(range_name): int(count) for range_name, count in duration_counts.items()}
            elif dataset == 'punctuality_analysis':
                # Enhanced punctuality analysis using real data
                df = self.data.copy()
                if df.empty or 'check_in' not in df or 'expected_check_in' not in df:
                    return {
                        'breakdown': {'Early': 0, 'On Time': 0, 'Late': 0},
                        'trends': {},
                        'day_time': {},
                        'outliers': {'most_punctual': [], 'least_punctual': []},
                        'deviation_distribution': {}
                    }
                # Calculate deviation in minutes
                df['deviation'] = (pd.to_datetime(df['check_in']) - pd.to_datetime(df['expected_check_in'])).dt.total_seconds() / 60
                # Categorize
                def categorize(dev):
                    if pd.isna(dev):
                        return 'On Time'
                    if dev < -5:
                        return 'Early'
                    elif dev > 5:
                        return 'Late'
                    else:
                        return 'On Time'
                df['punctuality'] = df['deviation'].apply(categorize)
                # Breakdown
                breakdown_counts = df['punctuality'].value_counts().to_dict()
                total = len(df)
                breakdown = {}
                for cat in ['Early', 'On Time', 'Late']:
                    count = breakdown_counts.get(cat, 0)
                    percent = round(count / total * 100, 1) if total else 0
                    avg_dev = df[df['punctuality'] == cat]['deviation'].mean()
                    if pd.isna(avg_dev):
                        avg_dev_str = '-'
                    else:
                        avg_dev_str = f"{avg_dev:+.0f} min" if cat != 'On Time' else f"±{abs(avg_dev):.0f} min"
                    breakdown[cat] = {
                        'count': count,
                        'percent': percent,
                        'avg_deviation': avg_dev_str
                    }
                # Trends (by day)
                df['day'] = pd.to_datetime(df['check_in']).dt.day_name()
                trends = {}
                for cat in ['Early', 'On Time', 'Late']:
                    trends[cat] = df[df['punctuality'] == cat].groupby('day').size().reindex([
                        'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'
                    ], fill_value=0).tolist()
                # Day-of-week & time-of-day
                df['hour'] = pd.to_datetime(df['check_in']).dt.hour
                def time_slot(h):
                    if 5 <= h < 12: return 'Morning'
                    if 12 <= h < 17: return 'Afternoon'
                    return 'Evening'
                df['time_slot'] = df['hour'].apply(time_slot)
                day_time = {}
                for slot in ['Morning', 'Afternoon', 'Evening']:
                    slot_counts = df[df['time_slot'] == slot].groupby('day').size().reindex([
                        'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'
                    ], fill_value=0).tolist()
                    day_time[slot] = slot_counts
                # Outliers (top/least punctual by avg deviation)
                tutor_dev = df.groupby('tutor_name')['deviation'].mean().sort_values()
                most_punctual = tutor_dev.abs().sort_values().head(3).index.tolist()
                least_punctual = tutor_dev.abs().sort_values(ascending=False).head(3).index.tolist()
                # Deviation distribution
                bins = [-float('inf'), -15, -5, 5, 15, float('inf')]
                labels = ['Early >15min', 'Early 5-15min', 'On Time ±5min', 'Late 5-15min', 'Late >15min']
                df['dev_bucket'] = pd.cut(df['deviation'], bins=bins, labels=labels)
                dev_dist = df['dev_bucket'].value_counts().reindex(labels, fill_value=0).to_dict()
                return {
                    'breakdown': breakdown,
                    'trends': trends,
                    'day_time': day_time,
                    'outliers': {
                        'most_punctual': most_punctual,
                        'least_punctual': least_punctual
                    },
                    'deviation_distribution': dev_dist
                }
            elif dataset == 'avg_session_duration_per_tutor':
                # Average session duration per tutor
                avg_duration = self.data.groupby('tutor_name')['shift_hours'].mean()
                return {str(tutor): float(duration) for tutor, duration in avg_duration.items()}
            elif dataset == 'tutor_consistency_score':
                # Calculate consistency score based on regular check-ins
                tutor_consistency = {}
                for tutor_name in self.data['tutor_name'].unique():
                    tutor_data = self.data[self.data['tutor_name'] == tutor_name]
                    if len(tutor_data) > 1:
                        # Calculate variance in session durations as consistency measure
                        variance = tutor_data['shift_hours'].var()
                        # Convert to a 0-100 score (lower variance = higher consistency)
                        max_variance = 4.0  # Assume max variance of 4 hours
                        consistency_score = max(0, 100 - (variance / max_variance * 100))
                        tutor_consistency[str(tutor_name)] = float(consistency_score)
                    else:
                        tutor_consistency[str(tutor_name)] = 50.0  # Default score for single session
                return tutor_consistency
            elif dataset == 'cumulative_checkins':
                # Cumulative check-ins over time
                daily_checkins = self.data.groupby('date').size()
                cumulative = daily_checkins.cumsum()
                return {str(date): int(count) for date, count in cumulative.items()}
            elif dataset == 'cumulative_hours':
                # Cumulative hours over time
                daily_hours = self.data.groupby('date')['shift_hours'].sum()
                cumulative = daily_hours.cumsum()
                return {str(date): float(hours) for date, hours in cumulative.items()}
            elif dataset == 'session_duration_vs_checkin_hour':
                return self.get_session_duration_vs_checkin_hour()
            else:
                return {}
        except Exception as e:
            logging.error(f"Error in get_chart_data for dataset '{dataset}': {e}")
            return {}

    def get_all_logs(self):
        """
        Get all logs in a format suitable for the frontend.
        """
        if self.data.empty:
            return []
        
        logs = []
        for _, row in self.data.iterrows():
            logs.append({
                'tutor_id': row.get('tutor_id'),
                'tutor_name': row.get('tutor_name'),
                'check_in': row.get('check_in').strftime('%Y-%m-%d %H:%M') if not pd.isna(row.get('check_in')) else None,
                'check_out': row.get('check_out').strftime('%Y-%m-%d %H:%M') if not pd.isna(row.get('check_out')) else None,
                'shift_hours': float(row.get('shift_hours')) if not pd.isna(row.get('shift_hours')) else None,
                'snapshot_in': row.get('snapshot_in'),
                'snapshot_out': row.get('snapshot_out')
            })
        
        return logs

    def log_admin_action(self, action, target_user_email=None, details=""):
        """Log admin actions for audit trail"""
        from flask import request, session
        from datetime import datetime
        import os
        import pandas as pd
        try:
            # Try to get current user from session
            current_user = session.get('user')
            if not current_user:
                return
            audit_file = 'logs/audit_log.csv'
            os.makedirs(os.path.dirname(audit_file), exist_ok=True)
            audit_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'admin_email': current_user.get('email', 'unknown'),
                'action': action,
                'target_user_email': target_user_email or '',
                'details': details,
                'ip_address': request.remote_addr if request else '',
                'user_agent': request.headers.get('User-Agent', '') if request else ''
            }
            # Load existing audit log or create new one
            if os.path.exists(audit_file):
                audit_df = pd.read_csv(audit_file)
            else:
                audit_df = pd.DataFrame(columns=[
                    'timestamp', 'admin_email', 'action', 'target_user_email', 
                    'details', 'ip_address', 'user_agent'
                ])
            audit_df = pd.concat([audit_df, pd.DataFrame([audit_entry])], ignore_index=True)
            audit_df.to_csv(audit_file, index=False)
        except Exception as e:
            print(f"Error logging admin action: {e}")

# Global instance
analytics = TutorAnalytics()