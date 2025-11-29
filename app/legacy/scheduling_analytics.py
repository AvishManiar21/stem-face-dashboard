import pandas as pd
import numpy as np
import os
from datetime import datetime

class SchedulingAnalytics:
    def __init__(self, custom_data=None):
        self.appointments_file = 'data/core/appointments.csv'
        self.tutors_file = 'data/core/tutors.csv'
        self.users_file = 'data/core/users.csv'
        if custom_data is not None:
            self.data = custom_data
        else:
            self.data = self.load_data()

    def load_data(self):
        try:
            # Try loading from Core Appointments first
            df_appt = pd.DataFrame()
            if os.path.exists(self.appointments_file):
                df_appt = pd.read_csv(self.appointments_file)
            
            # If Core is empty, try Legacy Face Log
            if df_appt.empty:
                legacy_file = 'data/legacy/face_log.csv'
                if os.path.exists(legacy_file):
                    # print(f"Loading data from {legacy_file}")
                    df_legacy = pd.read_csv(legacy_file)
                    if not df_legacy.empty:
                        # Map Legacy columns to expected schema
                        df_legacy['start_time_dt'] = pd.to_datetime(df_legacy['check_in'], errors='coerce')
                        df_legacy['end_time_dt'] = pd.to_datetime(df_legacy['check_out'], errors='coerce')
                        
                        # Ensure duration_hours exists
                        if 'shift_hours' in df_legacy.columns:
                            df_legacy['duration_hours'] = pd.to_numeric(df_legacy['shift_hours'], errors='coerce').fillna(0)
                        else:
                            df_legacy['duration_hours'] = (df_legacy['end_time_dt'] - df_legacy['start_time_dt']).dt.total_seconds() / 3600
                        
                        # Basic fields
                        df_legacy['date'] = df_legacy['start_time_dt'].dt.date
                        df_legacy['hour'] = df_legacy['start_time_dt'].dt.hour
                        df_legacy['day_of_week'] = df_legacy['start_time_dt'].dt.day_name()
                        df_legacy['month'] = df_legacy['start_time_dt'].dt.month
                        df_legacy['status'] = 'completed' # Assume log entries are completed sessions
                        
                        # Ensure tutor_id is string
                        df_legacy['tutor_id'] = df_legacy['tutor_id'].astype(str)
                        
                        return df_legacy

            if df_appt.empty:
                return pd.DataFrame()
            
            # Load Tutors and Users to get Tutor Names (Only for Core data)
            if os.path.exists(self.tutors_file) and os.path.exists(self.users_file):
                df_tutors = pd.read_csv(self.tutors_file)
                df_users = pd.read_csv(self.users_file)
                
                # Merge Tutors with Users
                df_tutor_users = pd.merge(df_tutors, df_users, on='user_id', how='left')
                df_tutor_users['tutor_name'] = df_tutor_users['first_name'] + ' ' + df_tutor_users['last_name']
                
                # Merge Appointments with Tutor Names
                # Ensure tutor_id types match
                df_appt['tutor_id'] = df_appt['tutor_id'].astype(str)
                df_tutor_users['tutor_id'] = df_tutor_users['tutor_id'].astype(str)
                
                df_appt = pd.merge(df_appt, df_tutor_users[['tutor_id', 'tutor_name']], on='tutor_id', how='left')
            else:
                df_appt['tutor_name'] = 'Unknown Tutor ' + df_appt['tutor_id'].astype(str)

            # Fill missing tutor names
            df_appt['tutor_name'] = df_appt['tutor_name'].fillna('Unknown Tutor')

            # Process Dates
            # Combine date and time safely
            df_appt['start_time_dt'] = pd.to_datetime(df_appt['appointment_date'] + ' ' + df_appt['start_time'], errors='coerce')
            df_appt['end_time_dt'] = pd.to_datetime(df_appt['appointment_date'] + ' ' + df_appt['end_time'], errors='coerce')
            
            # Calculate duration in hours
            df_appt['duration_hours'] = (df_appt['end_time_dt'] - df_appt['start_time_dt']).dt.total_seconds() / 3600
            
            # Drop invalid dates
            df_appt = df_appt.dropna(subset=['start_time_dt', 'end_time_dt'])
            
            df_appt['duration_hours'] = (df_appt['end_time_dt'] - df_appt['start_time_dt']).dt.total_seconds() / 3600
            
            df_appt['date'] = df_appt['start_time_dt'].dt.date
            df_appt['hour'] = df_appt['start_time_dt'].dt.hour
            df_appt['day_of_week'] = df_appt['start_time_dt'].dt.day_name()
            df_appt['month'] = df_appt['start_time_dt'].dt.month
            
            return df_appt
        except Exception as e:
            print(f"Error loading scheduling data: {e}")
            return pd.DataFrame()

    def get_chart_data(self, dataset):
        if self.data.empty:
            return {}
            
        try:
            if dataset == 'checkins_per_tutor': # Mapped to Appointments per Tutor
                return self.data.groupby('tutor_name').size().to_dict()
                
            elif dataset == 'hours_per_tutor': # Mapped to Scheduled Hours
                return self.data.groupby('tutor_name')['duration_hours'].sum().to_dict()
                
            elif dataset == 'daily_checkins': # Daily Appointments
                daily_data = self.data.groupby('date').size()
                return {str(date): int(count) for date, count in daily_data.items()}
                
            elif dataset == 'daily_hours': # Daily Scheduled Hours
                daily_data = self.data.groupby('date')['duration_hours'].sum()
                return {str(date): float(count) for date, count in daily_data.items()}
                
            elif dataset == 'hourly_checkins_dist': # Hourly Distribution
                hourly_data = self.data.groupby('hour').size()
                return {str(hour): int(count) for hour, count in hourly_data.items()}
                
            elif dataset == 'monthly_hours':
                monthly_data = self.data.groupby('month')['duration_hours'].sum()
                return {str(month): float(hours) for month, hours in monthly_data.items()}
                
            elif dataset == 'avg_hours_per_day_of_week':
                daily_avg = self.data.groupby('day_of_week')['duration_hours'].mean()
                return {str(day): float(avg) for day, avg in daily_avg.items()}
                
            elif dataset == 'checkins_per_day_of_week':
                daily_counts = self.data.groupby('day_of_week').size()
                return {str(day): int(count) for day, count in daily_counts.items()}
                
            elif dataset == 'hourly_activity_by_day':
                grouped = self.data.groupby(['day_of_week', 'hour']).size().unstack(fill_value=0)
                if grouped is None or grouped.empty:
                    return {}
                full_hours = list(range(24))
                for h in full_hours:
                    if h not in grouped.columns:
                        grouped[h] = 0
                grouped = grouped[sorted(grouped.columns)]
                result = {}
                for day in grouped.index.tolist():
                    day_series = grouped.loc[day]
                    result[str(day)] = {f"{int(hour):02d}:00": int(day_series[hour]) for hour in grouped.columns}
                return result
                
            elif dataset == 'session_duration_distribution':
                duration_ranges = pd.cut(self.data['duration_hours'], 
                                       bins=[0, 0.5, 1, 1.5, 2, float('inf')], 
                                       labels=['0-30m', '30m-1h', '1h-1.5h', '1.5h-2h', '2h+'])
                duration_counts = duration_ranges.value_counts()
                return {str(range_name): int(count) for range_name, count in duration_counts.items()}
                
            elif dataset == 'punctuality_analysis':
                # Since we don't have actual vs expected, we'll return dummy data or status breakdown
                # Let's return Status breakdown instead
                status_counts = self.data['status'].value_counts().to_dict()
                return {
                    'breakdown': {k: {'count': v, 'percent': 0} for k, v in status_counts.items()},
                    'trends': {},
                    'day_time': {},
                    'outliers': {'most_punctual': [], 'least_punctual': []},
                    'deviation_distribution': {}
                }
                
            return {}
        except Exception as e:
            print(f"Error in get_chart_data for dataset '{dataset}': {e}")
            return {}

    def get_dashboard_summary(self):
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
            
        total_appt = len(self.data)
        total_hours = round(self.data['duration_hours'].sum(), 1)
        active_tutors = self.data['tutor_id'].nunique()
        avg_duration = round(self.data['duration_hours'].mean(), 2)
        
        daily_hours = self.data.groupby('date')['duration_hours'].sum()
        avg_daily_hours = round(daily_hours.mean(), 2) if not daily_hours.empty else '—'
        
        peak_hour = int(self.data['hour'].mode()[0]) if not self.data['hour'].isna().all() else '—'
        top_day = str(daily_hours.idxmax()) if not daily_hours.empty else '—'
        
        # Top tutor
        top_tutor = self.data.groupby('tutor_name')['duration_hours'].sum().idxmax()
        
        return {
            'total_checkins': total_appt, # Labelled as checkins in frontend, but means appointments
            'total_hours': total_hours,
            'active_tutors': active_tutors,
            'avg_session_duration': avg_duration,
            'avg_daily_hours': avg_daily_hours,
            'peak_checkin_hour': peak_hour,
            'top_day': top_day,
            'top_tutor_current_month': top_tutor,
        }

    def get_day_status(self, day_data):
        if day_data.empty:
            return 'inactive'
        total_hours = day_data['duration_hours'].sum()
        if total_hours >= 10:
            return 'high_activity'
        elif total_hours >= 5:
            return 'normal'
        else:
            return 'low_activity'

    def day_has_issues(self, day_data):
        return False

    def get_session_status(self, session):
        return session.get('status', 'scheduled')
