"""
Shift Scheduling System for Tutor Face Recognition Dashboard
Handles shift creation, assignment, and monitoring
"""

import os
import pandas as pd
from datetime import datetime, timedelta, time
from analytics import TutorAnalytics
from auth import get_current_user

# Shift data files
SHIFTS_FILE = 'logs/shifts.csv'
SHIFT_ASSIGNMENTS_FILE = 'logs/shift_assignments.csv'

def ensure_shift_files():
    """Ensure shift data files exist with proper structure"""
    os.makedirs(os.path.dirname(SHIFTS_FILE), exist_ok=True)
    
    # Create shifts file if it doesn't exist
    if not os.path.exists(SHIFTS_FILE):
        shifts_df = pd.DataFrame(columns=[
            'shift_id', 'shift_name', 'start_time', 'end_time', 
            'days_of_week', 'created_by', 'created_at', 'active'
        ])
        shifts_df.to_csv(SHIFTS_FILE, index=False)
    
    # Create shift assignments file if it doesn't exist
    if not os.path.exists(SHIFT_ASSIGNMENTS_FILE):
        assignments_df = pd.DataFrame(columns=[
            'assignment_id', 'shift_id', 'tutor_id', 'tutor_name', 
            'start_date', 'end_date', 'assigned_by', 'assigned_at', 'active'
        ])
        assignments_df.to_csv(SHIFT_ASSIGNMENTS_FILE, index=False)

def load_shifts():
    """Load all shifts from CSV"""
    ensure_shift_files()
    try:
        df = pd.read_csv(SHIFTS_FILE)
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        return df
    except Exception as e:
        print(f"Error loading shifts: {e}")
        return pd.DataFrame(columns=[
            'shift_id', 'shift_name', 'start_time', 'end_time', 
            'days_of_week', 'created_by', 'created_at', 'active'
        ])

def load_shift_assignments():
    """Load all shift assignments from CSV"""
    ensure_shift_files()
    try:
        df = pd.read_csv(SHIFT_ASSIGNMENTS_FILE)
        if not df.empty:
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
            df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
            df['assigned_at'] = pd.to_datetime(df['assigned_at'], errors='coerce')
        return df
    except Exception as e:
        print(f"Error loading shift assignments: {e}")
        return pd.DataFrame(columns=[
            'assignment_id', 'shift_id', 'tutor_id', 'tutor_name', 
            'start_date', 'end_date', 'assigned_by', 'assigned_at', 'active'
        ])

def create_shift(shift_name, start_time, end_time, days_of_week):
    """Create a new shift template"""
    try:
        current_user = get_current_user()
        if not current_user:
            return False, "User not authenticated"
        
        shifts_df = load_shifts()
        
        # Generate new shift ID
        shift_id = f"SHIFT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create new shift record
        new_shift = {
            'shift_id': shift_id,
            'shift_name': shift_name,
            'start_time': start_time,
            'end_time': end_time,
            'days_of_week': days_of_week,  # Comma-separated: "Monday,Tuesday,Wednesday"
            'created_by': current_user.get('email'),
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        
        # Add to dataframe
        new_shift_df = pd.DataFrame([new_shift])
        shifts_df = pd.concat([shifts_df, new_shift_df], ignore_index=True)
        
        # Save to CSV
        shifts_df.to_csv(SHIFTS_FILE, index=False)
        
        # Log admin action
        TutorAnalytics().log_admin_action(
            action="CREATE_SHIFT",
            details=f"Created shift '{shift_name}' ({start_time}-{end_time}) for {days_of_week}"
        )
        
        return True, f"Shift '{shift_name}' created successfully"
        
    except Exception as e:
        return False, f"Error creating shift: {str(e)}"

def assign_tutor_to_shift(shift_id, tutor_id, tutor_name, start_date, end_date=None):
    """Assign a tutor to a shift for a specific period"""
    try:
        current_user = get_current_user()
        if not current_user:
            return False, "User not authenticated"
        
        assignments_df = load_shift_assignments()
        
        # Generate new assignment ID
        assignment_id = f"ASSIGN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create new assignment record
        new_assignment = {
            'assignment_id': assignment_id,
            'shift_id': shift_id,
            'tutor_id': tutor_id,
            'tutor_name': tutor_name,
            'start_date': start_date,
            'end_date': end_date or (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),  # Default 1 year
            'assigned_by': current_user.get('email'),
            'assigned_at': datetime.now().isoformat(),
            'active': True
        }
        
        # Add to dataframe
        new_assignment_df = pd.DataFrame([new_assignment])
        assignments_df = pd.concat([assignments_df, new_assignment_df], ignore_index=True)
        
        # Save to CSV
        assignments_df.to_csv(SHIFT_ASSIGNMENTS_FILE, index=False)
        
        # Log admin action
        TutorAnalytics().log_admin_action(
            action="ASSIGN_SHIFT",
            target_user_email=tutor_name,
            details=f"Assigned tutor {tutor_name} (ID: {tutor_id}) to shift {shift_id} from {start_date} to {end_date or 'ongoing'}"
        )
        
        return True, f"Tutor {tutor_name} assigned to shift successfully"
        
    except Exception as e:
        return False, f"Error assigning tutor to shift: {str(e)}"

def get_upcoming_shifts(days_ahead=7, page=1, per_page=12, exclude_today=True):
    """Get upcoming shifts for the next N days with pagination"""
    try:
        shifts_df = load_shifts()
        assignments_df = load_shift_assignments()
        
        if shifts_df.empty or assignments_df.empty:
            return {
                'shifts': [],
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_shifts': 0,
                    'total_pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }
        
        # Filter active shifts and assignments
        active_shifts = shifts_df[shifts_df['active'] == True]
        active_assignments = assignments_df[assignments_df['active'] == True]
        
        upcoming_shifts = []
        today = datetime.now().date()
        
        for days in range(days_ahead):
            check_date = today + timedelta(days=days)
            
            # Skip today if exclude_today is True
            if exclude_today and check_date == today:
                continue
                
            day_name = check_date.strftime('%A')
            
            # Find shifts for this day of week
            day_shifts = active_shifts[active_shifts['days_of_week'].str.contains(day_name, na=False)]
            
            for _, shift in day_shifts.iterrows():
                # Find assignments for this shift that are active on this date
                # Convert datetime columns to date for comparison
                shift_assignments = active_assignments[
                    (active_assignments['shift_id'] == shift['shift_id']) &
                    (active_assignments['start_date'].dt.date <= check_date) &
                    (active_assignments['end_date'].dt.date >= check_date)
                ]
                
                for _, assignment in shift_assignments.iterrows():
                    upcoming_shifts.append({
                        'date': check_date.strftime('%Y-%m-%d'),
                        'day_name': day_name,
                        'shift_id': shift['shift_id'],
                        'shift_name': shift['shift_name'],
                        'start_time': shift['start_time'],
                        'end_time': shift['end_time'],
                        'tutor_id': assignment['tutor_id'],
                        'tutor_name': assignment['tutor_name'],
                        'assignment_id': assignment['assignment_id']
                    })
        
        # Sort by date and time
        upcoming_shifts = sorted(upcoming_shifts, key=lambda x: (x['date'], x['start_time']))
        
        # Pagination calculations
        total_shifts = len(upcoming_shifts)
        total_pages = (total_shifts + per_page - 1) // per_page if per_page > 0 else 0

        # Clamp page into valid range when there are results
        if total_pages > 0:
            if page < 1:
                page = 1
            if page > total_pages:
                page = total_pages
        else:
            # No results; normalize page to 1
            page = 1

        start_idx = (page - 1) * per_page if per_page > 0 else 0
        end_idx = start_idx + per_page if per_page > 0 else 0
        paginated_shifts = upcoming_shifts[start_idx:end_idx]

        return {
            'shifts': paginated_shifts,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_shifts': total_shifts,
                'total_pages': total_pages,
                'has_next': total_pages > 0 and page < total_pages,
                'has_prev': total_pages > 0 and page > 1
            }
        }
        
    except Exception as e:
        print(f"Error getting upcoming shifts: {e}")
        return {'shifts': [], 'pagination': {}}

def check_late_checkins(face_log_df):
    """Check for late check-ins or early check-outs based on scheduled shifts"""
    try:
        upcoming_shifts_data = get_upcoming_shifts(1)  # Check today's shifts
        upcoming_shifts = upcoming_shifts_data.get('shifts', [])
        alerts = []
        
        today = datetime.now().date()
        today_shifts = [s for s in upcoming_shifts if s['date'] == today.strftime('%Y-%m-%d')]
        
        for shift in today_shifts:
            tutor_id = shift['tutor_id']
            shift_start = datetime.strptime(shift['start_time'], '%H:%M').time()
            shift_end = datetime.strptime(shift['end_time'], '%H:%M').time()
            
            # Find tutor's check-ins for today
            tutor_logs = face_log_df[
                (face_log_df['tutor_id'].astype(str) == str(tutor_id)) &
                (face_log_df['check_in'].dt.date == today)
            ]
            
            if tutor_logs.empty:
                # No check-in found
                alerts.append({
                    'type': 'missing_checkin',
                    'tutor_name': shift['tutor_name'],
                    'tutor_id': tutor_id,
                    'shift_name': shift['shift_name'],
                    'expected_time': shift['start_time'],
                    'message': f"{shift['tutor_name']} has not checked in for {shift['shift_name']} shift (expected at {shift['start_time']})"
                })
            else:
                latest_checkin = tutor_logs['check_in'].max()
                checkin_time = latest_checkin.time()
                
                # Check if late (more than 15 minutes)
                shift_start_dt = datetime.combine(today, shift_start)
                late_threshold = shift_start_dt + timedelta(minutes=15)
                
                if latest_checkin > late_threshold:
                    minutes_late = int((latest_checkin - shift_start_dt).total_seconds() / 60)
                    alerts.append({
                        'type': 'late_checkin',
                        'tutor_name': shift['tutor_name'],
                        'tutor_id': tutor_id,
                        'shift_name': shift['shift_name'],
                        'expected_time': shift['start_time'],
                        'actual_time': checkin_time.strftime('%H:%M'),
                        'minutes_late': minutes_late,
                        'message': f"{shift['tutor_name']} checked in {minutes_late} minutes late for {shift['shift_name']} shift"
                    })
                
                # Check for early checkout if there's a checkout time
                if not tutor_logs['check_out'].isna().all():
                    latest_checkout = tutor_logs['check_out'].max()
                    if pd.notna(latest_checkout):
                        checkout_time = latest_checkout.time()
                        shift_end_dt = datetime.combine(today, shift_end)
                        early_threshold = shift_end_dt - timedelta(minutes=15)
                        
                        if latest_checkout < early_threshold:
                            minutes_early = int((shift_end_dt - latest_checkout).total_seconds() / 60)
                            alerts.append({
                                'type': 'early_checkout',
                                'tutor_name': shift['tutor_name'],
                                'tutor_id': tutor_id,
                                'shift_name': shift['shift_name'],
                                'expected_time': shift['end_time'],
                                'actual_time': checkout_time.strftime('%H:%M'),
                                'minutes_early': minutes_early,
                                'message': f"{shift['tutor_name']} checked out {minutes_early} minutes early from {shift['shift_name']} shift"
                            })
        
        return alerts
        
    except Exception as e:
        print(f"Error checking late check-ins: {e}")
        return []

def get_all_shifts_with_assignments():
    """Get shifts that have actual schedule assignments, ordered by day and time"""
    try:
        shifts_df = load_shifts()
        assignments_df = load_shift_assignments()
        
        if shifts_df.empty:
            return []
        
        shifts_list = []
        
        for _, shift in shifts_df.iterrows():
            # Get assignments for this shift
            shift_assignments = assignments_df[
                (assignments_df['shift_id'] == shift['shift_id']) &
                (assignments_df['active'] == True)
            ]
            
            # Only include shifts that have actual assignments
            if shift_assignments.empty:
                continue
            
            # Get working days from actual assignments
            working_days = []
            if not shift_assignments.empty:
                # Get unique day names from assignments
                day_names = shift_assignments['day_name'].unique()
                # Sort days in proper order
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                working_days = [day for day in day_order if day in day_names]
            
            shift_data = shift.to_dict()
            shift_data['working_days'] = working_days
            shifts_list.append(shift_data)
        
        # Sort shifts by day and time
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        def sort_key(shift):
            # Get the first working day (primary sort)
            first_day = shift['working_days'][0] if shift['working_days'] else 'Sunday'
            day_index = day_order.index(first_day)
            
            # Get start time (secondary sort)
            start_time = shift['start_time']
            
            return (day_index, start_time)
        
        # Sort by day first, then by start time
        shifts_list.sort(key=sort_key)
        
        return shifts_list
        
    except Exception as e:
        print(f"Error getting shifts: {e}")
        return []

def deactivate_shift(shift_id):
    """Deactivate a shift"""
    try:
        shifts_df = load_shifts()
        shifts_df.loc[shifts_df['shift_id'] == shift_id, 'active'] = False
        shifts_df.to_csv(SHIFTS_FILE, index=False)
        
        # Also deactivate all assignments for this shift
        assignments_df = load_shift_assignments()
        assignments_df.loc[assignments_df['shift_id'] == shift_id, 'active'] = False
        assignments_df.to_csv(SHIFT_ASSIGNMENTS_FILE, index=False)
        
        # Log admin action
        TutorAnalytics().log_admin_action(
            action="DEACTIVATE_SHIFT",
            details=f"Deactivated shift {shift_id} and all its assignments"
        )
        
        return True, "Shift deactivated successfully"
        
    except Exception as e:
        return False, f"Error deactivating shift: {str(e)}"

def remove_tutor_assignment(assignment_id):
    """Remove a tutor from a shift assignment"""
    try:
        assignments_df = load_shift_assignments()
        assignment = assignments_df[assignments_df['assignment_id'] == assignment_id]
        
        if assignment.empty:
            return False, "Assignment not found"
        
        assignments_df.loc[assignments_df['assignment_id'] == assignment_id, 'active'] = False
        assignments_df.to_csv(SHIFT_ASSIGNMENTS_FILE, index=False)
        
        # Log admin action
        tutor_name = assignment.iloc[0]['tutor_name']
        shift_id = assignment.iloc[0]['shift_id']
        TutorAnalytics().log_admin_action(
            action="REMOVE_SHIFT_ASSIGNMENT",
            target_user_email=tutor_name,
            details=f"Removed tutor {tutor_name} from shift {shift_id}"
        )
        
        return True, "Tutor removed from shift successfully"
        
    except Exception as e:
        return False, f"Error removing tutor assignment: {str(e)}"