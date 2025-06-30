from flask import Flask, request, jsonify, send_file, redirect, url_for, flash, session, send_from_directory
import pandas as pd
from datetime import datetime, timedelta
import os
import io
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from analytics import TutorAnalytics
import shifts
import logging
from auto_logger import start_auto_logger, add_today_logs

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global flag to track if app has been initialized
_app_initialized = False

def initialize_app_once():
    """Initialize the application once"""
    global _app_initialized
    if not _app_initialized:
        try:
            # Add some today logs if none exist
            today = datetime.now().strftime('%Y-%m-%d')
            if os.path.exists('logs/face_log.csv'):
                df = pd.read_csv('logs/face_log.csv')
                today_logs = df[df['check_in'].str.startswith(today, na=False)]
                if len(today_logs) == 0:
                    logger.info("No today logs found, adding some...")
                    add_today_logs(3)
            
            # Start auto-logger
            start_auto_logger()
            logger.info("Auto-logger started")
            _app_initialized = True
        except Exception as e:
            logger.error(f"Error initializing app: {e}")

# Mock user data for demo purposes
MOCK_USERS = {
    'admin@example.com': {
        'user_id': 'admin_001',
        'email': 'admin@example.com',
        'full_name': 'Admin User',
        'role': 'admin',
        'active': True,
        'created_at': '2024-01-01T00:00:00Z',
        'last_login': '2024-01-15T10:30:00Z'
    },
    'test@example.com': {
        'user_id': 'tutor_001',
        'email': 'test@example.com',
        'full_name': 'Test Tutor',
        'role': 'tutor',
        'active': True,
        'created_at': '2024-01-02T00:00:00Z',
        'last_login': '2024-01-15T09:15:00Z'
    }
}

CSV_FILE = 'logs/face_log.csv'
SNAPSHOTS_DIR = 'static/snapshots'

# User management file
USERS_FILE = 'logs/users.csv'

def ensure_users_file():
    """Ensure users file exists with proper structure"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        users_df = pd.DataFrame(columns=[
            'user_id', 'email', 'full_name', 'role', 'created_at', 'last_login', 'active'
        ])
        # Create default admin user
        default_admin = {
            'user_id': 'ADMIN001',
            'email': 'admin@example.com',
            'full_name': 'System Administrator',
            'role': 'admin',
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat(),
            'active': True
        }
        users_df = pd.concat([users_df, pd.DataFrame([default_admin])], ignore_index=True)
        users_df.to_csv(USERS_FILE, index=False)

def load_users():
    """Load all users from CSV"""
    ensure_users_file()
    try:
        df = pd.read_csv(USERS_FILE)
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
            df['last_login'] = pd.to_datetime(df['last_login'], errors='coerce')
        return df
    except Exception as e:
        print(f"Error loading users: {e}")
        return pd.DataFrame(columns=[
            'user_id', 'email', 'full_name', 'role', 'created_at', 'last_login', 'active'
        ])

def get_current_user():
    """Get current user from session"""
    user_email = session.get('user_email')
    if user_email and user_email in MOCK_USERS:
        return MOCK_USERS[user_email]
    return None

def log_admin_action(action, target_user_email=None, details=""):
    """Log admin actions for audit trail"""
    try:
        current_user = get_current_user()
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
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
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

def send_email_notification(to_email, subject, message):
    """Send email notification (placeholder for SMTP integration)"""
    try:
        # This is a placeholder - in production, configure SMTP settings
        print(f"EMAIL NOTIFICATION TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"MESSAGE: {message}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def load_data():
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty: 
            raise FileNotFoundError 
    except FileNotFoundError:
        columns = ['tutor_id', 'tutor_name', 'check_in', 'check_out', 'shift_hours', 'snapshot_in', 'snapshot_out']
        df = pd.DataFrame(columns=columns)
        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
        os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
        return df

    df['check_in'] = pd.to_datetime(df['check_in'], errors='coerce')
    df['check_out'] = pd.to_datetime(df['check_out'], errors='coerce')
    
    if 'shift_hours' not in df.columns:
        valid_times = df['check_in'].notna() & df['check_out'].notna()
        df.loc[valid_times, 'shift_hours'] = (df.loc[valid_times, 'check_out'] - df.loc[valid_times, 'check_in']).dt.total_seconds() / 3600
    else:
        df['shift_hours'] = pd.to_numeric(df['shift_hours'], errors='coerce')
        mask_recalc = df['shift_hours'].isna() & df['check_in'].notna() & df['check_out'].notna()
        df.loc[mask_recalc, 'shift_hours'] = (df.loc[mask_recalc, 'check_out'] - df.loc[mask_recalc, 'check_in']).dt.total_seconds() / 3600
        
    df['shift_hours'] = df['shift_hours'].fillna(0).round(2)

    for col in ['snapshot_in', 'snapshot_out']:
        if col not in df.columns:
            df[col] = ''

    df['snapshot_in'] = df['snapshot_in'].fillna('').astype(str).apply(
        lambda x: x if x.startswith('snapshots/') or not x or x.startswith('/') else 'snapshots/' + os.path.basename(x)
    )
    df['snapshot_out'] = df['snapshot_out'].fillna('').astype(str).apply(
        lambda x: x if x.startswith('snapshots/') or not x or x.startswith('/') else 'snapshots/' + os.path.basename(x)
    )

    df = df.dropna(subset=['check_in'])
    if df.empty:
        return df

    df['date'] = df['check_in'].dt.date
    df['month_year'] = df['check_in'].dt.to_period('M').astype(str)
    df['day_name'] = df['check_in'].dt.day_name()
    df['hour'] = df['check_in'].dt.hour
    df['check_in_time_of_day'] = df['check_in'].dt.time 
    
    return df

@app.route('/')
def index():
    """Serve the main dashboard page"""
    # Initialize app on first request
    initialize_app_once()
    return send_from_directory('templates', 'dashboard.html')

@app.route('/charts')
def charts_page():
    """Serve the charts page"""
    return send_from_directory('templates', 'charts.html')

@app.route('/calendar')
def calendar_view():
    """Serve the calendar page"""
    return send_from_directory('templates', 'calendar.html')

@app.route('/admin/users')
def admin_users():
    """Serve the admin users page"""
    return send_from_directory('templates', 'admin_users.html')

@app.route('/admin/audit-logs')
def admin_audit_logs():
    """Serve the admin audit logs page"""
    return send_from_directory('templates', 'admin_audit_logs.html')

@app.route('/admin/shifts')
def admin_shifts():
    """Serve the admin shifts page"""
    return send_from_directory('templates', 'admin_shifts.html')

@app.route('/login')
def login_page():
    """Serve the login page"""
    return send_from_directory('templates', 'login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/login')

# API Endpoints

@app.route('/api/user-info')
def api_user_info():
    """Get current user information"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'user_id': user['user_id'],
        'email': user['email'],
        'full_name': user['full_name'],
        'role': user['role']
    })

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """Get dashboard data"""
    try:
        analytics = TutorAnalytics(face_log_file='logs/face_log_with_expected.csv')
        # Get logs for collapsible view
        logs_for_collapsible_view = analytics.get_logs_for_collapsible_view()
        # Get summary data
        summary = analytics.get_dashboard_summary()
        # Get alerts
        alerts = analytics.generate_alerts()
        return jsonify({
            'logs_for_collapsible_view': logs_for_collapsible_view,
            'summary': summary,
            'alerts': alerts
        })
    except Exception as e:
        print("DASHBOARD ERROR:", e)
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'error': 'Failed to load dashboard data'}), 500

@app.route('/dashboard-data')
def dashboard_data():
    """Alias for /api/dashboard-data for frontend compatibility"""
    return api_dashboard_data()

@app.route('/api/calendar-data')
def api_calendar_data():
    """Get calendar data"""
    try:
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        calendar_data = analytics.get_calendar_data(year, month)
        return jsonify(calendar_data)
    except Exception as e:
        logger.error(f"Error getting calendar data: {e}")
        return jsonify({'error': 'Failed to load calendar data'}), 500

@app.route('/api/upcoming-shifts')
def api_upcoming_shifts():
    """Get upcoming shifts"""
    try:
        upcoming_shifts = shifts.get_upcoming_shifts()
        return jsonify(upcoming_shifts)
    except Exception as e:
        logger.error(f"Error getting upcoming shifts: {e}")
        return jsonify([])

# Admin API Endpoints

@app.route('/api/admin/users')
def api_admin_users():
    """Get all users for admin"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(list(MOCK_USERS.values()))

@app.route('/api/admin/tutors')
def api_admin_tutors():
    """Get all tutors for shift assignment"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    tutors = [u for u in MOCK_USERS.values() if u['role'] in ['tutor', 'lead_tutor']]
    return jsonify(tutors)

@app.route('/api/admin/shifts')
def api_admin_shifts():
    """Get all shifts for admin management"""
    try:
        all_shifts = shifts.get_all_shifts_with_assignments()
        upcoming_shifts = shifts.get_upcoming_shifts()
        return jsonify({
            'shifts': all_shifts,
            'upcoming': upcoming_shifts
        })
    except Exception as e:
        logger.error(f"Error getting shifts: {e}")
        return jsonify({'shifts': [], 'upcoming': []})

@app.route('/api/admin/audit-logs')
def api_admin_audit_logs():
    """Get audit logs for admin"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        
        logs = analytics.get_audit_logs(page, per_page)
        return jsonify(logs)
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        return jsonify({'error': 'Failed to load audit logs'}), 500

# Admin POST endpoints

@app.route('/api/admin/create-user', methods=['POST'])
def api_admin_create_user():
    """Create a new user"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    # In a real app, you would save to database
    # For demo, we'll just return success
    return jsonify({'message': 'User created successfully'})

@app.route('/api/admin/edit-user', methods=['POST'])
def api_admin_edit_user():
    """Edit a user"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    # In a real app, you would update database
    return jsonify({'message': 'User updated successfully'})

@app.route('/api/admin/delete-user', methods=['POST'])
def api_admin_delete_user():
    """Delete a user"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    # In a real app, you would delete from database
    return jsonify({'message': 'User deleted successfully'})

@app.route('/api/admin/change-role', methods=['POST'])
def api_admin_change_role():
    """Change user role"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    # In a real app, you would update database
    return jsonify({'message': 'Role updated successfully'})

@app.route('/api/admin/create-shift', methods=['POST'])
def api_admin_create_shift():
    """Create a new shift"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    # In a real app, you would save to database
    return jsonify({'message': 'Shift created successfully'})

@app.route('/api/admin/assign-shift', methods=['POST'])
def api_admin_assign_shift():
    """Assign tutor to shift"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    # In a real app, you would save to database
    return jsonify({'message': 'Tutor assigned successfully'})

@app.route('/api/admin/activate-shift', methods=['POST'])
def api_admin_activate_shift():
    """Activate a shift"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    # In a real app, you would update database
    return jsonify({'message': 'Shift activated successfully'})

@app.route('/api/admin/deactivate-shift', methods=['POST'])
def api_admin_deactivate_shift():
    """Deactivate a shift"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    # In a real app, you would update database
    return jsonify({'message': 'Shift deactivated successfully'})

@app.route('/api/admin/populate-audit-logs', methods=['POST'])
def api_admin_populate_audit_logs():
    """Populate sample audit logs"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # In a real app, you would add sample data to database
    return jsonify({'message': 'Sample audit logs added successfully'})

# Authentication endpoint
@app.route('/login', methods=['POST'])
def login():
    """Handle login"""
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Simple demo authentication
    if email in MOCK_USERS:
        # In demo, accept any password
        session['user_email'] = email
        return redirect('/')
    else:
        flash('Invalid credentials', 'error')
        return redirect('/login')

# Chart data endpoints
@app.route('/chart-data', methods=['GET', 'POST'])
def chart_data():
    """Alias for /api/chart-data for frontend compatibility"""
    try:
        if request.method == 'POST':
            req = request.json or {}
            dataset = req.get('dataset') or req.get('chartKey') or 'checkins_per_tutor'
            grid_mode = req.get('grid') or req.get('mode') == 'grid'
            max_date = req.get('max_date')
        else:
            dataset = request.args.get('dataset') or request.args.get('chartKey') or 'checkins_per_tutor'
            grid_mode = request.args.get('grid') or request.args.get('mode') == 'grid'
            max_date = request.args.get('max_date')

        # Parse max_date if provided
        if max_date:
            try:
                max_date_parsed = pd.to_datetime(max_date)
            except Exception:
                max_date_parsed = None
        else:
            max_date_parsed = None

        analytics = TutorAnalytics(face_log_file='logs/face_log_with_expected.csv', max_date=max_date_parsed)

        if grid_mode:
            # Return all datasets needed for grid mode
            return jsonify({
                "checkins_per_tutor": analytics.get_chart_data("checkins_per_tutor"),
                "hours_per_tutor": analytics.get_chart_data("hours_per_tutor"),
                "daily_checkins": analytics.get_chart_data("daily_checkins"),
                "hourly_checkins_dist": analytics.get_chart_data("hourly_checkins_dist"),
            })
        else:
            chart_data = analytics.get_chart_data(dataset)
            return jsonify({dataset: chart_data})
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        return jsonify({'error': 'Failed to load chart data'}), 500

@app.route('/upcoming-shifts')
def upcoming_shifts():
    try:
        from shifts import get_upcoming_shifts
        
        # Get pagination parameters from query string
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        exclude_today = request.args.get('exclude_today', 'true').lower() == 'true'
        
        # Get upcoming shifts for the next 7 days with pagination
        result = get_upcoming_shifts(days_ahead=7, page=page, per_page=per_page, exclude_today=exclude_today)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in /upcoming-shifts: {e}")
        return jsonify({'shifts': [], 'pagination': {}}), 500

# File download endpoint
@app.route('/download-log')
def download_log():
    """Download log file"""
    try:
        # Get logs and create CSV
        analytics = TutorAnalytics(face_log_file='logs/face_log_with_expected.csv')
        logs = analytics.get_all_logs()
        df = pd.DataFrame(logs)
        
        # Create temporary file
        filename = f"tutor_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join('logs', filename)
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        df.to_csv(filepath, index=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        logger.error(f"Error downloading log: {e}")
        return jsonify({'error': 'Failed to download log'}), 500

# Check-in endpoint
@app.route('/check-in', methods=['POST'])
def check_in():
    """Handle manual check-in"""
    try:
        # Get form data
        tutor_id = request.form.get('tutor_id')
        tutor_name = request.form.get('tutor_name')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        shift_hours = request.form.get('shift_hours')
        snapshot_in = request.form.get('snapshot_in')
        snapshot_out = request.form.get('snapshot_out')
        
        # In a real app, you would save to database
        # For demo, we'll just return success
        
        flash('Check-in recorded successfully', 'success')
        return redirect('/')
    except Exception as e:
        logger.error(f"Error recording check-in: {e}")
        flash('Error recording check-in', 'error')
        return redirect('/')

@app.route('/get-tutors')
def get_tutors():
    """Get all tutors for frontend"""
    try:
        # Get unique tutors from face_log data
        analytics = TutorAnalytics(face_log_file='logs/face_log_with_expected.csv')
        df = analytics.data
        if df.empty:
            return jsonify([])
        
        tutors = df[['tutor_id', 'tutor_name']].drop_duplicates().to_dict('records')
        return jsonify(tutors)
    except Exception as e:
        logger.error(f"Error getting tutors: {e}")
        return jsonify([])

if __name__ == '__main__':
    if not os.path.exists(os.path.dirname(CSV_FILE)): os.makedirs(os.path.dirname(CSV_FILE))
    if not os.path.exists(SNAPSHOTS_DIR): os.makedirs(SNAPSHOTS_DIR)
    app.run(debug=True, host='0.0.0.0', port=5000)

