from flask import Flask, request, jsonify, send_file, redirect, url_for, flash, session, send_from_directory, make_response, render_template
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
from auth import authenticate_user
from auth_utils import USERS_FILE, hash_password
import simplejson as sjson
from supabase import create_client
from dotenv import load_dotenv
from forecasting_routes import forecasting_bp

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Register forecasting blueprint
app.register_blueprint(forecasting_bp)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global flag to track if app has been initialized (no demo seeding)
_app_initialized = False

def initialize_app_once():
    """Initialize the application once (no demo data, no auto-logger)."""
    global _app_initialized
    if not _app_initialized:
        try:
            _app_initialized = True
        except Exception as e:
            logger.error(f"Error initializing app: {e}")

# No mock users in production

CSV_FILE = 'logs/face_log.csv'
SNAPSHOTS_DIR = 'static/snapshots'

# User management via auth_utils.USERS_FILE and auth_utils.hash_password

def ensure_users_file():
    """Ensure users file exists with proper structure"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        users_df = pd.DataFrame(columns=[
            'user_id', 'email', 'full_name', 'role', 'created_at', 'last_login', 'active', 'password_hash'
        ])
        # Create default admin user
        default_admin = {
            'user_id': 'ADMIN001',
            'email': 'admin@example.com',
            'full_name': 'System Administrator',
            'role': 'admin',
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat(),
            'active': True,
            'password_hash': hash_password('admin123')
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
            'user_id', 'email', 'full_name', 'role', 'created_at', 'last_login', 'active', 'password_hash'
        ])

def get_current_user():
    """Get current user from session (supports Supabase and legacy CSV)"""
    # Supabase Auth: user info is stored in session['user']
    if 'user' in session:
        user = session['user']
        # Try to provide a unified user dict for frontend
        return {
            'user_id': user.get('id') or user.get('user_id'),
            'email': user.get('email'),
            'full_name': user.get('user_metadata', {}).get('full_name', '') if 'user_metadata' in user else '',
            'role': user.get('user_metadata', {}).get('role', 'tutor') if 'user_metadata' in user else 'tutor',
            'active': True
        }
    # Legacy CSV Auth fallback
    user_email = session.get('user_email')
    if not user_email:
        return None
    df = load_users()
    user_row = df[df['email'] == user_email]
    if not user_row.empty:
        return user_row.iloc[0].to_dict()
    return None

def send_email_notification(to_email, subject, message):
    """Send email notification (placeholder for SMTP integration)"""
    try:
        # This is a placeholder - in production, configure SMTP settings
        print(f"EMAIL NOTIFICATION TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"MESSAGE: {message}")
        
        # TODO: Implement actual SMTP integration
        # Example SMTP configuration:
        # import smtplib
        # from email.mime.text import MIMEText
        # from email.mime.multipart import MIMEMultipart
        # 
        # msg = MIMEMultipart()
        # msg['From'] = 'noreply@tutordashboard.com'
        # msg['To'] = to_email
        # msg['Subject'] = subject
        # msg.attach(MIMEText(message, 'plain'))
        # 
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login('your-email@gmail.com', 'your-app-password')
        # server.send_message(msg)
        # server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_shift_alert_email(tutor_email, tutor_name, alert_type, details):
    """Send specific shift-related alert emails"""
    subject_map = {
        'late_checkin': f'Late Check-in Alert - {tutor_name}',
        'early_checkout': f'Early Check-out Alert - {tutor_name}',
        'short_shift': f'Short Shift Alert - {tutor_name}',
        'overlapping': f'Overlapping Shifts Alert - {tutor_name}',
        'missed_shift': f'Missed Shift Alert - {tutor_name}',
        'no_checkout': f'Missing Check-out Alert - {tutor_name}'
    }
    
    subject = subject_map.get(alert_type, f'Shift Alert - {tutor_name}')
    
    message = f"""
Dear {tutor_name},

This is an automated alert from the Tutor Dashboard regarding your shift:

ALERT TYPE: {alert_type.replace('_', ' ').title()}
DETAILS: {details}

Please review your schedule and take appropriate action.

Best regards,
Tutor Dashboard System
    """
    
    return send_email_notification(tutor_email, subject, message)

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

@app.route('/admin/users')
def admin_users():
    """Serve the users page for all roles (admin, manager, lead_tutor, tutor)"""
    user = get_current_user()
    if not user:
        return redirect(url_for('dashboard'))
    return render_template('admin_users.html', user=user)

@app.route('/admin/audit-logs')
def admin_audit_logs():
    """Serve the admin audit logs page"""
    return send_from_directory('templates', 'admin_audit_logs.html')

@app.route('/admin/shifts')
def admin_shifts():
    """Serve the admin shifts page"""
    return send_from_directory('templates', 'admin_shifts.html')

@app.route('/calendar')
def calendar_page():
    """Serve the attendance calendar page"""
    return render_template('calendar.html')

@app.route('/login')
def login_page():
    """Serve the login page"""
    # Render login.html with default email value
    return render_template('login.html', default_email=request.args.get('email', ''))

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
    """Get users list based on role:
    - admin/manager: all users
    - lead_tutor: all users (read-only)
    - tutor: only their own info
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 403
    df = load_users()
    if 'password_hash' in df.columns:
        df = df.drop(columns=['password_hash'])
    for col in ['created_at', 'last_login']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x.isoformat() if pd.notnull(x) else '')
    if user['role'] in ['admin', 'manager', 'lead_tutor']:
        users = df.fillna('').to_dict(orient='records')
        if user['role'] == 'lead_tutor':
            # Add a flag to indicate read-only
            for u in users:
                u['read_only'] = True
        return jsonify(users)
    elif user['role'] == 'tutor':
        user_row = df[df['email'] == user['email']]
        if user_row.empty:
            return jsonify([])
        return jsonify(user_row.fillna('').to_dict(orient='records'))
    else:
        return jsonify({'error': 'Unauthorized'}), 403

@app.route('/api/admin/tutors')
def api_admin_tutors():
    """Get all tutors for shift assignment (admin/manager only)"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        # Prefer Supabase users table if available
        if supabase:
            resp = supabase.table('users').select('user_id,email,full_name,role,active').in_('role', ['tutor','lead_tutor']).execute()
            records = resp.data or []
            return jsonify(records)
        # Fallback to CSV users file
        df = load_users()
        df = df[df['role'].isin(['tutor','lead_tutor'])]
        if 'password_hash' in df.columns:
            df = df.drop(columns=['password_hash'])
        return jsonify(df.fillna('').to_dict(orient='records'))
    except Exception as e:
        logger.error(f"Error fetching tutors: {e}")
        return jsonify([])

@app.route('/api/admin/shifts')
def api_admin_shifts():
    """Get all shifts for admin and manager only"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Get all shifts with assignments
        shifts_data = shifts.get_all_shifts_with_assignments()
        
        # Get upcoming shifts for the next 7 days
        upcoming_shifts_data = shifts.get_upcoming_shifts(days_ahead=7, page=1, per_page=50, exclude_today=False)
        
        return jsonify({
            'shifts': shifts_data,
            'upcoming_shifts': upcoming_shifts_data.get('shifts', [])
        })
    except Exception as e:
        logger.error(f"Error getting shifts: {e}")
        return jsonify({'error': 'Failed to load shifts'}), 500

@app.route('/api/admin/audit-logs')
def api_admin_audit_logs():
    """Get audit logs for admin, manager, and lead tutor (read-only for lead tutor)"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager', 'lead_tutor']:
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        analytics = TutorAnalytics()
        logs_result = analytics.get_audit_logs(page, per_page)
        logs = logs_result.get('logs', [])
        total = logs_result.get('total', len(logs))
        total_pages = (total + per_page - 1) // per_page if per_page else 1
        response_data = {
            'logs': logs,
            'total': total,
            'pagination': {
                'total': total,
                'total_pages': total_pages,
                'page': page,
                'per_page': per_page
            }
        }
        print(f"[DEBUG] API Response: {len(logs)} logs, total: {total}, pages: {total_pages}")
        return app.response_class(
            response=sjson.dumps(response_data, ignore_nan=True),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        return jsonify({'error': 'Failed to load audit logs'}), 500

# Admin POST endpoints

@app.route('/api/admin/create-user', methods=['POST'])
def api_admin_create_user():
    """Create a new user (admin/manager only)"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    if not data.get('password'):
        return jsonify({'error': 'Password is required'}), 400
    df = load_users()
    if data['email'] in df['email'].values:
        return jsonify({'error': 'User already exists'}), 400

    # Check if email already exists in Supabase Auth before creating
    if supabase:
        try:
            # Query Supabase Auth for existing user by email
            existing_user = None
            try:
                existing_user_resp = supabase.auth.admin.list_users(email=data['email'])
                if hasattr(existing_user_resp, 'users') and existing_user_resp.users:
                    existing_user = existing_user_resp.users[0]
            except Exception as check_e:
                print(f"Supabase Auth check exception: {check_e}")
            if existing_user:
                return jsonify({'error': 'A user with this email address already exists in Supabase Auth.'}), 400
            # Proceed with user creation as before
            response = supabase.auth.admin.create_user({
                "email": data['email'],
                "password": data['password'],
                "user_metadata": {
                    "role": data['role'],
                    "full_name": data['full_name']
                },
                "email_confirm": True
            })
            if not getattr(response, 'user', None):
                print(f"Supabase Auth error: {response}")
                return jsonify({'error': 'Failed to create user in Supabase Auth', 'details': str(response)}), 400
            try:
                db_result = supabase.table("users").insert({
                    "email": data['email'],
                    "role": data['role'],
                    "full_name": data['full_name'],
                    "created_at": datetime.now().isoformat()
                }).execute()
                print(f"Supabase DB insert result: {db_result}")
            except Exception as db_e:
                print(f"[Supabase DB] Failed to insert user into users table: {db_e}")
        except Exception as e:
            print(f"Supabase Auth exception: {e}")
            return jsonify({'error': f'Could not create user in Supabase Auth: {e}'}), 400
    else:
        return jsonify({'error': 'Supabase not configured'}), 500

    # 2. Add to users.csv as before
    new_user = {
        'user_id': f"U{int(datetime.now().timestamp())}",
        'email': data['email'],
        'full_name': data['full_name'],
        'role': data['role'],
        'created_at': datetime.now().isoformat(),
        'last_login': '',
        'active': data.get('active', True),
        'password_hash': hash_password(data['password'])
    }
    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
    df.to_csv(USERS_FILE, index=False)
    analytics = TutorAnalytics()
    analytics.log_admin_action('create_user', target_user_email=data.get('email'), details=f"Created user with role {data.get('role')}")
    return jsonify({'message': 'User created successfully'})

@app.route('/api/admin/edit-user', methods=['POST'])
def api_admin_edit_user():
    """Edit a user (admin/manager only, or tutor editing own info)"""
    user = get_current_user()
    data = request.get_json()
    df = load_users()
    idx = df.index[df['user_id'] == data['user_id']]
    if len(idx) == 0:
        return jsonify({'error': 'User not found'}), 404
    i = idx[0]
    # Admin/manager can edit anyone
    if user and user['role'] in ['admin', 'manager']:
        df.at[i, 'email'] = data['email']
        df.at[i, 'full_name'] = data['full_name']
        df.at[i, 'role'] = data['role']
        df.at[i, 'active'] = data.get('active', True)
        if data.get('password'):
            df.at[i, 'password_hash'] = hash_password(data['password'])
        df.to_csv(USERS_FILE, index=False)
        analytics = TutorAnalytics()
        analytics.log_admin_action('edit_user', target_user_email=data.get('email'), details=f"Edited user info for {data.get('user_id')}")
        return jsonify({'message': 'User updated successfully'})
    # Tutor can only edit their own info (password, maybe name)
    elif user and user['role'] == 'tutor' and df.at[i, 'email'] == user['email']:
        if data.get('full_name'):
            df.at[i, 'full_name'] = data['full_name']
        if data.get('password'):
            df.at[i, 'password_hash'] = hash_password(data['password'])
        df.to_csv(USERS_FILE, index=False)
        analytics = TutorAnalytics()
        analytics.log_admin_action('edit_user', target_user_email=data.get('email'), details=f"Tutor edited own info for {data.get('user_id')}")
        return jsonify({'message': 'User updated successfully'})
    else:
        return jsonify({'error': 'Unauthorized'}), 403

@app.route('/api/admin/delete-user', methods=['POST'])
def api_admin_delete_user():
    """Delete a user (admin only)"""
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    df = load_users()
    idx = df.index[df['user_id'] == data['user_id']]
    if len(idx) == 0:
        return jsonify({'error': 'User not found'}), 404
    email = df.at[idx[0], 'email']
    df = df.drop(idx)
    df.to_csv(USERS_FILE, index=False)
    analytics = TutorAnalytics()
    analytics.log_admin_action('delete_user', target_user_email=email, details=f"Deleted user")
    return jsonify({'message': 'User deleted successfully'})

@app.route('/api/admin/change-role', methods=['POST'])
def api_admin_change_role():
    """Change user role"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    new_role = data.get('role')
    if not user_id or not new_role:
        return jsonify({'error': 'Missing user_id or role'}), 400

    # Validate role
    valid_roles = ['tutor', 'lead_tutor', 'manager', 'admin']
    if new_role not in valid_roles:
        return jsonify({'error': 'Invalid role'}), 400

    # Load current user data
    import pandas as pd
    csv_path = 'logs/users.csv'
    df = pd.read_csv(csv_path)
    
    # Find target user
    target_user = df[df['user_id'].astype(str) == str(user_id)]
    if target_user.empty:
        return jsonify({'error': 'User not found'}), 404
    
    target_user = target_user.iloc[0]
    old_role = target_user['role']
    target_email = target_user['email']
    
    # Prevent changing your own role
    if target_email == user['email']:
        return jsonify({'error': 'You cannot change your own role'}), 400
    
    # Prevent demoting the last admin
    if old_role == 'admin' and new_role != 'admin':
        admin_count = len(df[df['role'] == 'admin'])
        if admin_count <= 1:
            return jsonify({'error': 'Cannot demote the last admin user'}), 400
    
    # Prevent managers from promoting to admin (only admins can create other admins)
    if user['role'] == 'manager' and new_role == 'admin':
        return jsonify({'error': 'Managers cannot promote users to admin'}), 403
    
    # Update CSV
    df.loc[df['user_id'].astype(str) == str(user_id), 'role'] = new_role
    df.to_csv(csv_path, index=False)

    # Update Supabase users table
    if supabase:
        try:
            supabase.table('users').update({'role': new_role}).eq('user_id', user_id).execute()
        except Exception as e:
            print(f"[Supabase DB] Failed to update user role: {e}")

    # Log admin action with more details
    analytics = TutorAnalytics()
    details = f"Changed role from {old_role} to {new_role} for user {target_email}"
    analytics.log_admin_action('change_role', target_user_email=target_email, details=details)
    
    return jsonify({
        'message': 'Role updated successfully',
        'old_role': old_role,
        'new_role': new_role,
        'user_name': target_user['full_name']
    })

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

@app.route('/api/admin/delete-supabase-user', methods=['POST'])
def api_admin_delete_supabase_user():
    """Delete a user from Supabase Auth and optionally from the users table (admin/manager only)"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not supabase:
        return jsonify({'error': 'Supabase not configured'}), 500
    try:
        # Find user in Supabase Auth
        user_resp = supabase.auth.admin.list_users(email=email)
        if hasattr(user_resp, 'users') and user_resp.users:
            user_id = user_resp.users[0].id
            supabase.auth.admin.delete_user(user_id)
            # Optionally, also remove from users table
            try:
                supabase.table("users").delete().eq("email", email).execute()
            except Exception as db_e:
                print(f"[Supabase DB] Failed to delete user from users table: {db_e}")
            return jsonify({'message': f'User {email} deleted from Supabase Auth and users table.'})
        else:
            return jsonify({'error': 'User not found in Supabase Auth.'}), 404
    except Exception as e:
        print(f"Supabase Auth delete exception: {e}")
        return jsonify({'error': f'Could not delete user from Supabase Auth: {e}'}), 400

@app.route('/api/admin/user-activate', methods=['POST'])
def api_admin_user_activate():
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    email = data.get('email')
    active = data.get('active')
    if not email or active is None:
        return jsonify({'error': 'Missing email or active'}), 400
    # Update CSV
    import pandas as pd
    csv_path = 'logs/users.csv'
    df = pd.read_csv(csv_path)
    if email not in df['email'].values:
        return jsonify({'error': 'User not found in CSV'}), 404
    df.loc[df['email'] == email, 'active'] = bool(active)
    df.to_csv(csv_path, index=False)
    # Update Supabase users table
    if supabase:
        try:
            supabase.table('users').update({'active': bool(active)}).eq('email', email).execute()
        except Exception as e:
            print(f"[Supabase DB] Failed to update user active status: {e}")
    # Optionally, disable in Supabase Auth (block login by checking active)
    # Log audit
    from datetime import datetime
    with open('logs/audit_log.csv', 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()},{user['email']},user_activate,Set active={active},,,,{email},\n")
    return jsonify({'success': True})

# Authentication endpoint
@app.route('/login', methods=['POST'])
def login():
    """Handle login"""
    email = request.form.get('email')
    password = request.form.get('password')
    success, message = authenticate_user(email, password)
    if success:
        # Store user in session (already handled by authenticate_user)
        return redirect('/')
    # On failure, re-render login page with inline error and preserved email
    flash(message or 'Invalid credentials', 'error')
    return render_template('login.html', default_email=email), 400

# Chart data endpoints
@app.route('/chart-data', methods=['GET', 'POST'])
def chart_data():
    """Handle chart data requests with proper form data support"""
    try:
        logger.info("Chart data request received")
        if request.method == 'POST':
            # Handle both JSON and form data
            if request.content_type and 'application/json' in request.content_type:
                req = request.json or {}
            else:
                req = request.form.to_dict() or {}
            
            dataset = req.get('dataset') or req.get('chartKey') or 'checkins_per_tutor'
            grid_mode = req.get('grid') or req.get('mode') == 'grid'
            max_date = req.get('max_date')
            
            # Extract filter parameters from form
            tutor_ids = req.get('tutor_ids', '')
            start_date = req.get('start_date')
            end_date = req.get('end_date')
            shift_start_hour = req.get('shift_start_hour', '0')
            shift_end_hour = req.get('shift_end_hour', '23')
        else:
            dataset = request.args.get('dataset') or request.args.get('chartKey') or 'checkins_per_tutor'
            grid_mode = request.args.get('grid') or request.args.get('mode') == 'grid'
            max_date = request.args.get('max_date')
            tutor_ids = request.args.get('tutor_ids', '')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            shift_start_hour = request.args.get('shift_start_hour', '0')
            shift_end_hour = request.args.get('shift_end_hour', '23')

        # Parse max_date if provided
        if max_date:
            try:
                max_date_parsed = pd.to_datetime(max_date)
            except Exception:
                max_date_parsed = None
        else:
            max_date_parsed = None

        # Parse other filter parameters
        tutor_ids_list = []
        if tutor_ids:
            try:
                tutor_ids_list = [int(tid.strip()) for tid in tutor_ids.split(',') if tid.strip()]
            except ValueError:
                tutor_ids_list = []
        
        start_date_parsed = None
        if start_date:
            try:
                start_date_parsed = pd.to_datetime(start_date)
            except Exception:
                start_date_parsed = None
                
        end_date_parsed = None
        if end_date:
            try:
                end_date_parsed = pd.to_datetime(end_date)
            except Exception:
                end_date_parsed = None

        # Check if this is a comparison mode request
        is_comparison_mode = req.get('mode') == 'comparison'
        comparison_type = req.get('comparisonType', 'time_period')
        
        # Initialize analytics with filters
        logger.info(f"Initializing analytics with max_date: {max_date_parsed}, comparison_mode: {is_comparison_mode}")
        try:
            analytics = TutorAnalytics(
                face_log_file='logs/face_log_with_expected.csv', 
                max_date=max_date_parsed
            )
            logger.info(f"Analytics initialized successfully. Data shape: {analytics.data.shape if hasattr(analytics.data, 'shape') else 'No shape attribute'}")
        except Exception as e:
            logger.error(f"Error initializing analytics: {e}")
            raise
        
        # Apply additional filters if provided
        filter_condition = (tutor_ids_list or start_date_parsed or end_date_parsed or 
            shift_start_hour != '0' or shift_end_hour != '23' or
            req.get('minHours') or req.get('maxHours') or req.get('minSessions') or 
            req.get('maxSessions') or req.get('sessionPattern') or req.get('timeOfDay') or
            req.get('punctualityFilter') or req.get('excludeWeekends'))
        
        logger.info(f"Filter condition result: {filter_condition}")
        logger.info(f"Individual conditions: tutor_ids_list={bool(tutor_ids_list)}, start_date_parsed={bool(start_date_parsed)}, end_date_parsed={bool(end_date_parsed)}")
        logger.info(f"Hour conditions: shift_start_hour={shift_start_hour}, shift_end_hour={shift_end_hour}")
        
        if filter_condition:
            
            logger.info(f"Applying filters - Original data shape: {analytics.data.shape}")
            logger.info(f"Filter parameters: tutor_ids={tutor_ids_list}, start_date={start_date_parsed}, end_date={end_date_parsed}")
            logger.info(f"Advanced filters: minHours={req.get('minHours')}, maxHours={req.get('maxHours')}, timeOfDay={req.get('timeOfDay')}")
            logger.info(f"Raw request data: {req}")
            
            # Filter the data based on the provided parameters
            df = analytics.data.copy()
            
            if tutor_ids_list:
                df = df[df['tutor_id'].isin(tutor_ids_list)]
            
            if start_date_parsed:
                df = df[df['check_in'] >= start_date_parsed]
                
            if end_date_parsed:
                df = df[df['check_in'] <= end_date_parsed]
            
            if shift_start_hour != '0' or shift_end_hour != '23':
                df['check_in_hour'] = df['check_in'].dt.hour
                df = df[(df['check_in_hour'] >= int(shift_start_hour)) & (df['check_in_hour'] <= int(shift_end_hour))]
            
            # Apply advanced filters
            if req.get('minHours'):
                try:
                    min_hours = float(req.get('minHours'))
                    df = df[df['shift_hours'] >= min_hours]
                except (ValueError, TypeError):
                    pass
            
            if req.get('maxHours'):
                try:
                    max_hours = float(req.get('maxHours'))
                    df = df[df['shift_hours'] <= max_hours]
                except (ValueError, TypeError):
                    pass
            
            if req.get('minSessions'):
                try:
                    min_sessions = int(req.get('minSessions'))
                    # Count sessions per tutor and filter
                    tutor_session_counts = df.groupby('tutor_id').size()
                    tutors_with_min_sessions = tutor_session_counts[tutor_session_counts >= min_sessions].index
                    df = df[df['tutor_id'].isin(tutors_with_min_sessions)]
                except (ValueError, TypeError):
                    pass
            
            if req.get('maxSessions'):
                try:
                    max_sessions = int(req.get('maxSessions'))
                    # Count sessions per tutor and filter
                    tutor_session_counts = df.groupby('tutor_id').size()
                    tutors_with_max_sessions = tutor_session_counts[tutor_session_counts <= max_sessions].index
                    df = df[df['tutor_id'].isin(tutors_with_max_sessions)]
                except (ValueError, TypeError):
                    pass
            
            if req.get('timeOfDay') and req.get('timeOfDay') != 'All Times':
                time_of_day = req.get('timeOfDay')
                df['check_in_hour'] = df['check_in'].dt.hour
                if time_of_day == 'Morning':
                    df = df[(df['check_in_hour'] >= 6) & (df['check_in_hour'] < 12)]
                elif time_of_day == 'Afternoon':
                    df = df[(df['check_in_hour'] >= 12) & (df['check_in_hour'] < 18)]
                elif time_of_day == 'Evening':
                    df = df[(df['check_in_hour'] >= 18) & (df['check_in_hour'] < 22)]
                elif time_of_day == 'Night':
                    df = df[(df['check_in_hour'] >= 22) | (df['check_in_hour'] < 6)]
            
            if req.get('excludeWeekends') == 'true':
                df = df[df['check_in'].dt.dayofweek < 5]  # Monday=0, Sunday=6
            
            # Create a new analytics instance with filtered data
            logger.info(f"Filtered data shape: {df.shape}")
            analytics = TutorAnalytics(face_log_file='logs/face_log_with_expected.csv', custom_data=df)

        if grid_mode:
            # Return all datasets needed for grid mode
            return jsonify({
                "checkins_per_tutor": analytics.get_chart_data("checkins_per_tutor"),
                "hours_per_tutor": analytics.get_chart_data("hours_per_tutor"),
                "daily_checkins": analytics.get_chart_data("daily_checkins"),
                "hourly_checkins_dist": analytics.get_chart_data("hourly_checkins_dist"),
            })
        else:
            logger.info(f"Generating chart data for dataset: {dataset}")
            try:
                chart_data = analytics.get_chart_data(dataset)
                logger.info(f"Chart data generated successfully. Keys: {list(chart_data.keys()) if isinstance(chart_data, dict) else 'Not a dict'}")
            except Exception as e:
                logger.error(f"Error generating chart data for dataset {dataset}: {e}")
                raise
            
            # Return data in the format expected by the frontend
            # Convert data to records, handling NaT values
            raw_records = []
            if hasattr(analytics.data, 'to_dict'):
                try:
                    # Convert NaT values to None for JSON serialization
                    df_clean = analytics.data.copy()
                    
                    # Handle all datetime columns and convert NaT to None
                    for col in df_clean.columns:
                        if df_clean[col].dtype == 'datetime64[ns]':
                            df_clean[col] = df_clean[col].where(pd.notna(df_clean[col]), None)
                        elif df_clean[col].dtype == 'object':
                            # Check if column contains datetime strings that might have NaT
                            df_clean[col] = df_clean[col].where(pd.notna(df_clean[col]), None)
                    
                    # Convert to records
                    raw_records = df_clean.to_dict('records')
                    
                    # Additional cleanup for any remaining NaT values
                    for record in raw_records:
                        for key, value in record.items():
                            if pd.isna(value):
                                record[key] = None
                                
                except Exception as e:
                    logger.error(f"Error converting data to records: {e}")
                    raw_records = []
            
            response_data = {
                "dataset": dataset,
                "chart_data": chart_data,
                "chart_type": "bar",  # Default chart type
                "title": f"{dataset.replace('_', ' ').title()}",
                "raw_records_for_chart_context": raw_records
            }
            
            # Handle comparison mode
            if is_comparison_mode:
                logger.info(f"Processing comparison mode: {comparison_type}")
                
                if comparison_type in ['time_period', 'time_periods']:
                    # Compare two time periods
                    period1_start = req.get('period1Start')
                    period1_end = req.get('period1End')
                    period2_start = req.get('period2Start')
                    period2_end = req.get('period2End')
                    
                    if period1_start and period1_end and period2_start and period2_end:
                        try:
                            # Create analytics for period 1
                            analytics_p1 = TutorAnalytics(
                                face_log_file='logs/face_log_with_expected.csv',
                                max_date=pd.to_datetime(period1_end)
                            )
                            analytics_p1.data = analytics_p1.data[
                                (analytics_p1.data['check_in'].dt.date >= pd.to_datetime(period1_start).date()) &
                                (analytics_p1.data['check_in'].dt.date <= pd.to_datetime(period1_end).date())
                            ]
                            
                            # Create analytics for period 2
                            analytics_p2 = TutorAnalytics(
                                face_log_file='logs/face_log_with_expected.csv',
                                max_date=pd.to_datetime(period2_end)
                            )
                            analytics_p2.data = analytics_p2.data[
                                (analytics_p2.data['check_in'].dt.date >= pd.to_datetime(period2_start).date()) &
                                (analytics_p2.data['check_in'].dt.date <= pd.to_datetime(period2_end).date())
                            ]
                            
                            # Generate chart data for both periods
                            chart_data_p1 = analytics_p1.get_chart_data(dataset)
                            chart_data_p2 = analytics_p2.get_chart_data(dataset)
                            
                            # Update response with comparison data
                            response_data = {
                                "dataset": dataset,
                                "primary_data": {
                                    "chart_data": chart_data_p1,
                                    "chart_type": "bar",
                                    "title": f"{dataset.replace('_', ' ').title()} - Period 1 ({period1_start} to {period1_end})"
                                },
                                "comparison_data": {
                                    "chart_data": chart_data_p2,
                                    "chart_type": "bar", 
                                    "title": f"{dataset.replace('_', ' ').title()} - Period 2 ({period2_start} to {period2_end})"
                                },
                                "comparison_mode": True,
                                "comparison_type": comparison_type,
                                "raw_records_for_chart_context": raw_records
                            }
                            
                        except Exception as e:
                            logger.error(f"Error processing time period comparison: {e}")
                            response_data["error"] = f"Comparison failed: {str(e)}"
                    else:
                        response_data["error"] = "Missing time period parameters for comparison"
                        
                elif comparison_type == 'tutors':
                    # Compare different tutors
                    tutor_ids = req.get('tutor_ids', '').split(',') if req.get('tutor_ids') else []
                    if len(tutor_ids) >= 2:
                        try:
                            # Split tutors into two groups
                            mid_point = len(tutor_ids) // 2
                            tutors_p1 = tutor_ids[:mid_point]
                            tutors_p2 = tutor_ids[mid_point:]
                            
                            # Create analytics for tutor group 1
                            analytics_p1 = TutorAnalytics(
                                face_log_file='logs/face_log_with_expected.csv',
                                max_date=max_date_parsed
                            )
                            analytics_p1.data = analytics_p1.data[analytics_p1.data['tutor_id'].isin(tutors_p1)]
                            
                            # Create analytics for tutor group 2
                            analytics_p2 = TutorAnalytics(
                                face_log_file='logs/face_log_with_expected.csv',
                                max_date=max_date_parsed
                            )
                            analytics_p2.data = analytics_p2.data[analytics_p2.data['tutor_id'].isin(tutors_p2)]
                            
                            # Generate chart data for both groups
                            chart_data_p1 = analytics_p1.get_chart_data(dataset)
                            chart_data_p2 = analytics_p2.get_chart_data(dataset)
                            
                            # Update response with comparison data
                            response_data = {
                                "dataset": dataset,
                                "primary_data": {
                                    "chart_data": chart_data_p1,
                                    "chart_type": "bar",
                                    "title": f"{dataset.replace('_', ' ').title()} - Group 1 ({len(tutors_p1)} tutors)"
                                },
                                "comparison_data": {
                                    "chart_data": chart_data_p2,
                                    "chart_type": "bar", 
                                    "title": f"{dataset.replace('_', ' ').title()} - Group 2 ({len(tutors_p2)} tutors)"
                                },
                                "comparison_mode": True,
                                "comparison_type": comparison_type,
                                "raw_records_for_chart_context": raw_records
                            }
                            
                        except Exception as e:
                            logger.error(f"Error processing tutor comparison: {e}")
                            response_data["error"] = f"Tutor comparison failed: {str(e)}"
                    else:
                        response_data["error"] = "Please select at least 2 tutors for comparison"
                        
                elif comparison_type == 'day_types':
                    # Compare weekdays vs weekends
                    try:
                        # Create analytics for weekdays
                        analytics_weekdays = TutorAnalytics(
                            face_log_file='logs/face_log_with_expected.csv',
                            max_date=max_date_parsed
                        )
                        analytics_weekdays.data = analytics_weekdays.data[
                            analytics_weekdays.data['day_of_week'].isin(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
                        ]
                        
                        # Create analytics for weekends
                        analytics_weekends = TutorAnalytics(
                            face_log_file='logs/face_log_with_expected.csv',
                            max_date=max_date_parsed
                        )
                        analytics_weekends.data = analytics_weekends.data[
                            analytics_weekends.data['day_of_week'].isin(['Saturday', 'Sunday'])
                        ]
                        
                        # Generate chart data for both day types
                        chart_data_weekdays = analytics_weekdays.get_chart_data(dataset)
                        chart_data_weekends = analytics_weekends.get_chart_data(dataset)
                        
                        # Update response with comparison data
                        response_data = {
                            "dataset": dataset,
                            "primary_data": {
                                "chart_data": chart_data_weekdays,
                                "chart_type": "bar",
                                "title": f"{dataset.replace('_', ' ').title()} - Weekdays"
                            },
                            "comparison_data": {
                                "chart_data": chart_data_weekends,
                                "chart_type": "bar", 
                                "title": f"{dataset.replace('_', ' ').title()} - Weekends"
                            },
                            "comparison_mode": True,
                            "comparison_type": comparison_type,
                            "raw_records_for_chart_context": raw_records
                        }
                        
                    except Exception as e:
                        logger.error(f"Error processing day types comparison: {e}")
                        response_data["error"] = f"Day types comparison failed: {str(e)}"
                        
                elif comparison_type == 'duration_ranges':
                    # Compare short vs long sessions
                    try:
                        # Create analytics for short sessions (<= 2 hours)
                        analytics_short = TutorAnalytics(
                            face_log_file='logs/face_log_with_expected.csv',
                            max_date=max_date_parsed
                        )
                        analytics_short.data = analytics_short.data[analytics_short.data['shift_hours'] <= 2.0]
                        
                        # Create analytics for long sessions (> 2 hours)
                        analytics_long = TutorAnalytics(
                            face_log_file='logs/face_log_with_expected.csv',
                            max_date=max_date_parsed
                        )
                        analytics_long.data = analytics_long.data[analytics_long.data['shift_hours'] > 2.0]
                        
                        # Generate chart data for both duration ranges
                        chart_data_short = analytics_short.get_chart_data(dataset)
                        chart_data_long = analytics_long.get_chart_data(dataset)
                        
                        # Update response with comparison data
                        response_data = {
                            "dataset": dataset,
                            "primary_data": {
                                "chart_data": chart_data_short,
                                "chart_type": "bar",
                                "title": f"{dataset.replace('_', ' ').title()} - Short Sessions (≤2h)"
                            },
                            "comparison_data": {
                                "chart_data": chart_data_long,
                                "chart_type": "bar", 
                                "title": f"{dataset.replace('_', ' ').title()} - Long Sessions (>2h)"
                            },
                            "comparison_mode": True,
                            "comparison_type": comparison_type,
                            "raw_records_for_chart_context": raw_records
                        }
                        
                    except Exception as e:
                        logger.error(f"Error processing duration ranges comparison: {e}")
                        response_data["error"] = f"Duration ranges comparison failed: {str(e)}"
                        
                else:
                    response_data["error"] = f"Unsupported comparison type: {comparison_type}"
            
            logger.info(f"Response data prepared successfully")
            
            # Add punctuality analysis if requested
            if dataset == 'punctuality_analysis' or req.get('include_punctuality'):
                try:
                    punctuality_data = analytics.get_chart_data('punctuality_analysis')
                    response_data["punctuality_analysis"] = punctuality_data
                except Exception as e:
                    logger.error(f"Error getting punctuality analysis: {e}")
                    response_data["punctuality_analysis"] = None
            
            return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        logger.error(f"Request data: {req if 'req' in locals() else 'No request data'}")
        return jsonify({'error': f'Failed to load chart data: {str(e)}'}), 500

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
        
        # --- Audit log entry ---
        audit_file = 'logs/audit_log.csv'
        import pandas as pd
        import os
        from datetime import datetime
        # Compose audit log row
        audit_entry = {
            'timestamp': check_in or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_email': session.get('user', {}).get('email', ''),
            'action': 'TUTOR_CHECK_IN',
            'details': f'{tutor_name} ({tutor_id}) checked in',
            'ip_address': request.remote_addr if request else '',
            'user_agent': request.headers.get('User-Agent', '') if request else ''
        }
        # Append to audit log
        if os.path.exists(audit_file):
            audit_df = pd.read_csv(audit_file)
        else:
            audit_df = pd.DataFrame(columns=['timestamp','user_email','action','details','ip_address','user_agent'])
        audit_df = pd.concat([audit_df, pd.DataFrame([audit_entry])], ignore_index=True)
        audit_df.to_csv(audit_file, index=False)
        # --- End audit log entry ---
        
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

@app.route('/export-punctuality-csv', methods=['POST'])
def export_punctuality_csv():
    """Export punctuality analysis as CSV for the selected tab and filters"""
    try:
        # Accept both form and JSON
        if request.content_type and 'application/json' in request.content_type:
            req = request.get_json() or {}
        else:
            req = request.form.to_dict() or {}
        tab = req.get('tab', 'breakdown')
        # Extract filters (same as /chart-data)
        dataset = 'punctuality_analysis'
        max_date = req.get('max_date')
        # Build analytics with filters
        analytics = TutorAnalytics(face_log_file='logs/face_log_with_expected.csv', max_date=pd.to_datetime(max_date) if max_date else None)
        pa = analytics.get_chart_data(dataset)
        import io
        output = io.StringIO()
        if tab == 'breakdown':
            output.write('Category,Count,Percentage,Avg Deviation\n')
            for cat in ['Early', 'On Time', 'Late']:
                b = pa['breakdown'].get(cat, {})
                output.write(f"{cat},{b.get('count','-')},{b.get('percent','-')},{b.get('avg_deviation','-')}\n")
            filename = 'punctuality_breakdown.csv'
        elif tab == 'trends':
            output.write('Day,Early,On Time,Late\n')
            days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            for i, day in enumerate(days):
                output.write(f"{day},{pa['trends'].get('Early',[0]*7)[i]},{pa['trends'].get('On Time',[0]*7)[i]},{pa['trends'].get('Late',[0]*7)[i]}\n")
            filename = 'punctuality_trends.csv'
        elif tab == 'daytime':
            output.write('Day,Slot,Sessions\n')
            days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            slots = ['Morning','Afternoon','Evening']
            for slot in slots:
                for i, day in enumerate(days):
                    val = pa['day_time'].get(slot, [0]*7)[i]
                    output.write(f"{day},{slot},{val}\n")
            filename = 'punctuality_by_day_time.csv'
        elif tab == 'outliers':
            output.write('Type,Tutors\n')
            output.write(f"Most Punctual,\"{','.join(pa['outliers'].get('most_punctual', []))}\"\n")
            output.write(f"Least Punctual,\"{','.join(pa['outliers'].get('least_punctual', []))}\"\n")
            filename = 'punctuality_top_performers.csv'
        elif tab == 'deviation':
            output.write('Deviation Bucket,Sessions\n')
            labels = ['Early >15min', 'Early 5-15min', 'On Time ±5min', 'Late 5-15min', 'Late >15min']
            for label in labels:
                output.write(f"{label},{pa['deviation_distribution'].get(label,0)}\n")
            filename = 'punctuality_deviation.csv'
        else:
            return jsonify({'error': 'Unknown export type'}), 400
        resp = make_response(output.getvalue())
        resp.headers['Content-Disposition'] = f'attachment; filename={filename}'
        resp.headers['Content-Type'] = 'text/csv'
        return resp
    except Exception as e:
        logger.error(f"Error exporting punctuality CSV: {e}")
        return jsonify({'error': 'Failed to export punctuality data'}), 500

@app.route('/api/lead-tutor/users')
def api_lead_tutor_users():
    """Get only the current user's info for lead_tutor role (future self-service)"""
    user = get_current_user()
    if not user or user['role'] != 'lead_tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    df = load_users()
    user_row = df[df['email'] == user['email']]
    if user_row.empty:
        return jsonify({'error': 'User not found'}), 404
    user_info = user_row.drop(columns=['password_hash']).fillna('').to_dict(orient='records')[0]
    return jsonify(user_info)

@app.route('/api/tutor/user')
def api_tutor_user():
    """Get only the current tutor's info (for profile/self-service)"""
    user = get_current_user()
    if not user or user['role'] != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    df = load_users()
    user_row = df[df['email'] == user['email']]
    if user_row.empty:
        return jsonify({'error': 'User not found'}), 404
    user_info = user_row.drop(columns=['password_hash']).fillna('').to_dict(orient='records')[0]
    return jsonify(user_info)

@app.route('/profile')
def profile():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    return render_template('profile.html', user=user)

@app.route('/api/profile', methods=['GET'])
def api_profile_get():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(user)

@app.route('/api/profile', methods=['POST'])
def api_profile_update():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    updated = False
    # Update name
    if 'full_name' in data and data['full_name'] != user['full_name']:
        # Update in CSV and Supabase users table
        # ... update logic ...
        updated = True
    # Update password
    if 'password' in data and data['password']:
        # Update in Supabase Auth if enabled, else CSV
        # ... update logic ...
        updated = True
    if updated:
        # Log audit
        # ... audit log logic ...
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'No changes'})

@app.route('/api/dashboard-alerts')
def api_dashboard_alerts():
    """Return dashboard alerts for the current user (or all users if admin/manager)"""
    user = get_current_user()
    if not user:
        return jsonify({'alerts': []})

    import pandas as pd
    from datetime import datetime, timedelta
    alerts = []
    face_log_path = 'logs/face_log_with_expected.csv'
    shifts_path = 'logs/shifts.csv'
    assignments_path = 'logs/shift_assignments.csv'

    try:
        face_log = pd.read_csv(face_log_path)
        shifts_df = pd.read_csv(shifts_path)
        assignments_df = pd.read_csv(assignments_path)
    except Exception as e:
        return jsonify({'alerts': [f'Error loading logs: {e}']})

    today = datetime.now().date()
    # Filter logs for today - use check_in column instead of timestamp
    today_logs = face_log[pd.to_datetime(face_log['check_in']).dt.date == today]

    # Only show relevant logs for non-admins
    if user['role'] not in ['admin', 'manager']:
        # Filter by tutor_id instead of user_email since we don't have user_email in this format
        today_logs = today_logs[today_logs['tutor_id'] == user.get('tutor_id', 0)]
        assignments_df = assignments_df[assignments_df['tutor_email'] == user['email']]

    # Late check-in: checked in after expected start time
    for _, row in today_logs.iterrows():
        if pd.notnull(row.get('expected_check_in')):
            try:
                checkin_time = datetime.strptime(row['check_in'], '%Y-%m-%d %H:%M:%S')
                expected_time = datetime.strptime(row['expected_check_in'], '%Y-%m-%d %H:%M:%S')
                if checkin_time > expected_time:
                    time_diff = (checkin_time - expected_time).total_seconds() / 60  # minutes
                    alert_msg = f"Late check-in: {row.get('tutor_name', 'Tutor')} (Expected {expected_time.strftime('%H:%M')}, Checked in {checkin_time.strftime('%H:%M')}, {time_diff:.0f} min late)"
                    alerts.append(alert_msg)
                    
                    # Send email notification for late check-in
                    if user['role'] in ['admin', 'manager']:
                        send_shift_alert_email(
                            f"{row.get('tutor_id', '')}@example.com",  # Generate email from tutor_id
                            row.get('tutor_name', 'Tutor'),
                            'late_checkin',
                            alert_msg
                        )
            except Exception as e:
                continue
    # Early check-out: checked out before expected end time
    for _, row in today_logs.iterrows():
        if pd.notnull(row.get('expected_check_out')) and pd.notnull(row.get('check_out')):
            try:
                checkout_time = datetime.strptime(row['check_out'], '%Y-%m-%d %H:%M:%S')
                expected_time = datetime.strptime(row['expected_check_out'], '%Y-%m-%d %H:%M:%S')
                if checkout_time < expected_time:
                    time_diff = (expected_time - checkout_time).total_seconds() / 60  # minutes
                    alert_msg = f"Early check-out: {row.get('tutor_name', 'Tutor')} (Expected {expected_time.strftime('%H:%M')}, Checked out {checkout_time.strftime('%H:%M')}, {time_diff:.0f} min early)"
                    alerts.append(alert_msg)
                    
                    # Send email notification for early check-out
                    if user['role'] in ['admin', 'manager']:
                        send_shift_alert_email(
                            f"{row.get('tutor_id', '')}@example.com",  # Generate email from tutor_id
                            row.get('tutor_name', 'Tutor'),
                            'early_checkout',
                            alert_msg
                        )
            except Exception as e:
                continue
    # Short shift: duration < 1 hour
    for _, row in today_logs.iterrows():
        if pd.notnull(row.get('check_out')) and row.get('shift_hours', 0) < 1.0:
            alert_msg = f"Short shift: {row.get('tutor_name', 'Tutor')} (Duration: {row.get('shift_hours', 0):.1f}h)"
            alerts.append(alert_msg)
            
            # Send email notification for short shift
            if user['role'] in ['admin', 'manager']:
                send_shift_alert_email(
                    f"{row.get('tutor_id', '')}@example.com",  # Generate email from tutor_id
                    row.get('tutor_name', 'Tutor'),
                    'short_shift',
                    alert_msg
                )
    
    # Missing check-outs: tutors who checked in but didn't check out
    for _, row in today_logs.iterrows():
        if pd.isna(row.get('check_out')):
            checkin_time = datetime.strptime(row['check_in'], '%Y-%m-%d %H:%M:%S')
            alert_msg = f"Missing check-out: {row.get('tutor_name', 'Tutor')} (Checked in at {checkin_time.strftime('%H:%M')})"
            alerts.append(alert_msg)
            
            # Send email notification for missing check-out
            if user['role'] in ['admin', 'manager']:
                send_shift_alert_email(
                    f"{row.get('tutor_id', '')}@example.com",  # Generate email from tutor_id
                    row.get('tutor_name', 'Tutor'),
                    'no_checkout',
                    alert_msg
                )
    
    # Overlapping sessions: check for overlapping assignments (simplified)
    # This would require more complex logic with shift assignments
    # For now, we'll skip this check as it's not critical for calendar functionality
    pass
    
    return jsonify({'alerts': alerts})

@app.route('/api/notification-settings', methods=['GET'])
def api_notification_settings():
    """Get notification settings for the current user"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Default notification settings
    settings = {
        'email_notifications': True,
        'late_checkin_alerts': True,
        'early_checkout_alerts': True,
        'short_shift_alerts': True,
        'overlapping_shift_alerts': True,
        'missing_checkout_alerts': True,
        'smtp_configured': False,  # Will be True when SMTP is properly configured
        'notification_email': user['email']
    }
    
    return jsonify(settings)

@app.route('/api/notification-settings', methods=['POST'])
def api_update_notification_settings():
    """Update notification settings"""
    user = get_current_user()
    if not user or user['role'] not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # In a real implementation, you would save these settings to a database
    # For now, we'll just return success
    updated_settings = {
        'email_notifications': data.get('email_notifications', True),
        'late_checkin_alerts': data.get('late_checkin_alerts', True),
        'early_checkout_alerts': data.get('early_checkout_alerts', True),
        'short_shift_alerts': data.get('short_shift_alerts', True),
        'overlapping_shift_alerts': data.get('overlapping_shift_alerts', True),
        'missing_checkout_alerts': data.get('missing_checkout_alerts', True),
        'notification_email': data.get('notification_email', user['email'])
    }
    
    # Log the settings update
    analytics = TutorAnalytics()
    analytics.log_admin_action('update_notification_settings', 
                              target_user_email=user['email'], 
                              details=f"Updated notification settings: {updated_settings}")
    
    return jsonify({'message': 'Notification settings updated successfully', 'settings': updated_settings})

@app.route('/api/calendar-data')
def api_calendar_data():
    """Get calendar data for attendance view"""
    try:
        import calendar
        from datetime import datetime, timedelta
        analytics = TutorAnalytics(face_log_file='logs/face_log_with_expected.csv')
        # Print first few check_in values for debugging
        logging.warning(f"First 5 check_in values: {analytics.data['check_in'].head().tolist()}")
        # Get current month and year
        now = datetime.now()
        year = request.args.get('year', now.year, type=int)
        month = request.args.get('month', now.month, type=int)
        # Get calendar data
        cal = calendar.monthcalendar(year, month)
        # Get attendance data for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        # Filter data for the month
        month_data = analytics.data[
            (analytics.data['check_in'] >= start_date) & 
            (analytics.data['check_in'] <= end_date)
        ]
        # Print number of rows after filtering
        logging.warning(f"Rows for {year}-{month:02d}: {len(month_data)}")
        # Group by date
        daily_data = {}
        for date in month_data['check_in'].dt.date.unique():
            day_data = month_data[month_data['check_in'].dt.date == date]
            daily_data[date] = {
                'sessions': int(len(day_data)),
                'total_hours': float(day_data['shift_hours'].sum()),
                'tutors': int(day_data['tutor_id'].nunique()),
                'status': str(analytics.get_day_status(day_data)),
                'has_issues': bool(analytics.day_has_issues(day_data)),
                'sessions_data': _serialize_sessions_data(day_data.to_dict('records'))
            }
        
        # Create calendar matrix with attendance data
        calendar_data = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append(None)  # Empty day
                else:
                    date = datetime(year, month, day).date()
                    day_info = daily_data.get(date, {
                        'sessions': 0,
                        'total_hours': 0.0,
                        'tutors': 0,
                        'status': 'inactive',
                        'has_issues': False,
                        'sessions_data': []
                    })
                    week_data.append({
                        'day': day,
                        'date': date.isoformat(),
                        **day_info
                    })
            calendar_data.append(week_data)
        
        # Convert calendar matrix to days object for frontend
        days = {}
        for week in calendar_data:
            for day in week:
                if day and day.get('day'):
                    days[day['day']] = {
                        'sessions': day['sessions'],
                        'total_hours': day['total_hours'],
                        'tutors': day['tutors'],
                        'status': day['status'],
                        'has_issues': day['has_issues'],
                        'sessions_data': day['sessions_data']
                    }
        
        return jsonify({
            'days': days,
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'prev_month': {'year': year if month > 1 else year - 1, 'month': month - 1 if month > 1 else 12},
            'next_month': {'year': year if month < 12 else year + 1, 'month': month + 1 if month < 12 else 1}
        })
        
    except Exception as e:
        logger.error(f"Error getting calendar data: {e}")
        return jsonify({'error': 'Failed to load calendar data'}), 500

def _serialize_sessions_data(sessions):
    """Helper function to serialize sessions data for JSON"""
    import numpy as np
    serialized = []
    for session in sessions:
        serialized_session = {}
        for key, value in session.items():
            if pd.isna(value):
                serialized_session[key] = None
            elif isinstance(value, (np.integer, np.int64)):
                serialized_session[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                serialized_session[key] = float(value)
            elif isinstance(value, (np.bool_, bool)):
                serialized_session[key] = bool(value)
            elif isinstance(value, (pd.Timestamp, datetime)):
                serialized_session[key] = value.isoformat() if pd.notna(value) else None
            else:
                serialized_session[key] = str(value) if value is not None else None
        serialized.append(serialized_session)
    return serialized

@app.route('/api/calendar-day-details')
def api_calendar_day_details():
    """Get detailed sessions for a specific day"""
    try:
        from datetime import datetime
        
        date_str = request.args.get('date')
        if not date_str:
            return jsonify({'error': 'Date parameter required'}), 400
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        analytics = TutorAnalytics(face_log_file='logs/face_log_with_expected.csv')
        
        # Filter data for the specific date
        day_data = analytics.data[analytics.data['check_in'].dt.date == target_date]
        
        sessions = []
        for _, session in day_data.iterrows():
            sessions.append({
                'tutor_id': session['tutor_id'],
                'tutor_name': session['tutor_name'],
                'check_in': session['check_in'].strftime('%H:%M'),
                'check_out': session['check_out'].strftime('%H:%M') if pd.notna(session['check_out']) else None,
                'shift_hours': session['shift_hours'],
                'status': analytics.get_session_status(session),
                'snapshot_in': session['snapshot_in'],
                'snapshot_out': session['snapshot_out']
            })
        
        return jsonify({
            'date': target_date.isoformat(),
            'sessions': sessions,
            'total_sessions': len(sessions),
            'total_hours': day_data['shift_hours'].sum(),
            'unique_tutors': day_data['tutor_id'].nunique()
        })
        
    except Exception as e:
        logger.error(f"Error getting day details: {e}")
        return jsonify({'error': 'Failed to load day details'}), 500

if __name__ == '__main__':
    if not os.path.exists(os.path.dirname(CSV_FILE)): os.makedirs(os.path.dirname(CSV_FILE))
    if not os.path.exists(SNAPSHOTS_DIR): os.makedirs(SNAPSHOTS_DIR)
    app.run(debug=True, host='0.0.0.0', port=5000)

