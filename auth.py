"""
Authentication module for Tutor Face Recognition Dashboard
Handles Supabase authentication and role-based access control
"""

import os
import logging
import hashlib
import secrets
from functools import wraps
from flask import session, request, jsonify, redirect, url_for, flash
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    logger.error("Supabase URL and Key must be set in environment variables")
    raise ValueError("Supabase URL and Key must be set in environment variables")

try:
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise

# Role hierarchy for access control
ROLE_HIERARCHY = {
    'tutor': 1,
    'lead_tutor': 2, 
    'manager': 3,
    'admin': 3  # Admin same level as manager
}

# Audit log file
AUDIT_LOG_FILE = 'logs/audit_log.csv'

def get_current_user():
    """Get current authenticated user from session"""
    if 'user' in session:
        return session['user']
    return None

def get_user_role(email=None):
    """Get user's role - current user if no email provided, or specific user by email"""
    if email:
        # Get role for specific user
        try:
            response = supabase.table('users').select('role').eq('email', email).execute()
            if response.data:
                return response.data[0].get('role', 'tutor')
        except Exception as e:
            logger.error(f"Error getting user role for {email}: {e}")
            return 'tutor'
    else:
        # Get current user's role
        user = get_current_user()
        if user and 'user_metadata' in user:
            return user['user_metadata'].get('role', 'tutor')
    return 'tutor'

def get_user_tutor_id():
    """Get current user's tutor_id for data filtering"""
    user = get_current_user()
    if user and 'user_metadata' in user:
        return user['user_metadata'].get('tutor_id')
    return None

def has_role_access(required_role):
    """Check if current user has required role access"""
    current_role = get_user_role()
    if not current_role:
        return False
    
    current_level = ROLE_HIERARCHY.get(current_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 999)
    
    return current_level >= required_level

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not get_current_user():
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('login'))
            
            if not has_role_access(required_role):
                if request.is_json:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def hash_password(password, salt=None):
    """Hash password with salt for secure storage"""
    if salt is None:
        salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt, password_hash.hex()

def verify_password(password, salt, stored_hash):
    """Verify password against stored hash"""
    try:
        _, computed_hash = hash_password(password, salt)
        return secrets.compare_digest(computed_hash, stored_hash)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def authenticate_user(email, password):
    """
    Hybrid authentication - tries Supabase Auth first, then custom users table
    """
    if not email or not password:
        return False, "Email and password are required"
    
    # First try Supabase Auth
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Store user in session
            session['user'] = {
                'id': response.user.id,
                'email': response.user.email,
                'user_metadata': response.user.user_metadata or {}
            }
            if hasattr(response, 'session') and response.session:
                session['access_token'] = response.session.access_token
            logger.info(f"User {email} authenticated via Supabase Auth")
            return True, "Login successful"
            
    except Exception as supabase_error:
        logger.warning(f"Supabase Auth failed for {email}: {supabase_error}")
        
        # If Supabase Auth fails, try custom users table
        try:
            # Query custom users table
            response = supabase.table('users').select('*').eq('email', email).execute()
            
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                
                # Verify password - handle both salt-based and legacy hash-only systems
                password_hash = user_data.get('password_hash', '')
                salt = user_data.get('salt', '')

                # If salt exists, use salt-based verification
                if salt:
                    password_valid = verify_password(password, salt, password_hash)
                else:
                    # Legacy system - try direct hash comparison (for existing users)
                    # This is a simple hash comparison for backward compatibility
                    import hashlib
                    simple_hash = hashlib.sha256(password.encode()).hexdigest()
                    password_valid = secrets.compare_digest(simple_hash, password_hash)

                if password_valid:
                    # Store user in session (mimicking Supabase Auth format)
                    session['user'] = {
                        'id': user_data['id'],
                        'email': user_data['email'],
                        'user_metadata': {
                            'role': user_data.get('role', 'tutor'),
                            'full_name': user_data.get('full_name', ''),
                            'tutor_id': user_data.get('tutor_id')
                        }
                    }
                    logger.info(f"User {email} authenticated via custom users table")
                    return True, "Login successful"
                else:
                    logger.warning(f"Invalid password for user {email}")
                    return False, "Invalid email or password"
            else:
                logger.warning(f"User {email} not found in custom users table")
                return False, "Invalid email or password"
                
        except Exception as custom_error:
            logger.error(f"Custom authentication error for {email}: {custom_error}")
            return False, f"Authentication error: {str(custom_error)}"
    
    return False, "Authentication failed"

def logout_user():
    """Logout current user"""
    try:
        # Sign out from Supabase
        supabase.auth.sign_out()
        
        # Clear session
        session.clear()
        logger.info("User logged out successfully")
        return True, "Logged out successfully"
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Clear session even if Supabase logout fails
        session.clear()
        return True, "Logged out successfully"

def validate_user_input(email, password, role, tutor_id=None, full_name=None):
    """Validate user input for registration and updates"""
    errors = []
    
    # Email validation
    if not email or '@' not in email:
        errors.append("Valid email is required")
    
    # Password validation
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    # Role validation
    if role not in ROLE_HIERARCHY:
        errors.append(f"Invalid role. Must be one of: {', '.join(ROLE_HIERARCHY.keys())}")
    
    # Tutor ID validation (optional)
    if tutor_id and not str(tutor_id).isdigit():
        errors.append("Tutor ID must be a number")
    
    return errors

def register_user(email, password, role='tutor', tutor_id=None, full_name=None):
    """Register new user (admin only function)"""
    # Validate input
    validation_errors = validate_user_input(email, password, role, tutor_id, full_name)
    if validation_errors:
        return False, f"Validation errors: {'; '.join(validation_errors)}"
    
    try:
        # Check if user already exists
        existing_user = supabase.table('users').select('id').eq('email', email).execute()
        if existing_user.data and len(existing_user.data) > 0:
            return False, f"User {email} already exists"
        
        # Hash password with salt
        salt, password_hash = hash_password(password)
        
        # Create user metadata
        user_metadata = {
            'role': role,
            'full_name': full_name or email.split('@')[0]
        }
        
        if tutor_id:
            user_metadata['tutor_id'] = tutor_id
            
        # Create user in custom users table
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'salt': salt,
            'role': role,
            'full_name': full_name or email.split('@')[0],
            'tutor_id': tutor_id,
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.table('users').insert(user_data).execute()
        
        if response.data:
            # Log admin action
            log_admin_action(
                action="CREATE_USER",
                target_user_email=email,
                details=f"Created user with role: {role}, tutor_id: {tutor_id or 'None'}"
            )
            logger.info(f"User {email} created successfully")
            return True, f"User {email} created successfully"
        else:
            logger.error(f"Failed to create user {email}")
            return False, "Failed to create user"
            
    except Exception as e:
        logger.error(f"Registration error for {email}: {e}")
        return False, f"Registration error: {str(e)}"

def update_user_role(user_id, new_role, tutor_id=None):
    """Update user role (admin only function)"""
    try:
        user_metadata = {'role': new_role}
        if tutor_id:
            user_metadata['tutor_id'] = tutor_id
            
        response = supabase.auth.admin.update_user_by_id(
            user_id,
            {"user_metadata": user_metadata}
        )
        
        if response.user:
            # Log admin action
            log_admin_action(
                action="UPDATE_USER_ROLE",
                target_user_email="Unknown",  # We'll improve this later
                details=f"Changed role to {new_role}, tutor_id: {tutor_id or 'None'}"
            )
            return True, "User role updated successfully"
        else:
            return False, "Failed to update user role"
            
    except Exception as e:
        return False, f"Update error: {str(e)}"

def get_all_users():
    """Get all users (admin only function)"""
    try:
        # Note: This requires admin privileges
        response = supabase.auth.admin.list_users()
        return response.users if response else []
    except Exception as e:
        # Silently handle permission errors to avoid console spam
        if "User not allowed" in str(e) or "permission" in str(e).lower():
            return []  # Return empty list for permission errors
        print(f"Error fetching users: {e}")
        return []

def filter_data_by_role(df, user_role=None, user_tutor_id=None):
    """Filter dataframe based on user role and permissions"""
    if not user_role:
        user_role = get_user_role()
    if not user_tutor_id:
        user_tutor_id = get_user_tutor_id()
    
    # Managers and admins see all data
    if user_role in ['manager', 'admin']:
        return df
    
    # Lead tutors see all data (can be restricted if needed)
    if user_role == 'lead_tutor':
        return df
    
    # Regular tutors only see their own data
    if user_role == 'tutor' and user_tutor_id:
        if 'tutor_id' in df.columns:
            return df[df['tutor_id'].astype(str) == str(user_tutor_id)]
    
    # If no matching conditions, return empty dataframe
    return df.iloc[0:0]  # Empty dataframe with same structure

def log_admin_action(action, target_user_email=None, details=None):
    """Log admin actions for audit trail"""
    try:
        current_user = get_current_user()
        if not current_user:
            return
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
        
        # Prepare audit log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'admin_user_id': current_user.get('id'),
            'admin_email': current_user.get('email'),
            'action': action,
            'target_user_email': target_user_email or '',
            'details': details or '',
            'ip_address': request.remote_addr if request else ''
        }
        
        # Load existing audit log or create new one
        try:
            audit_df = pd.read_csv(AUDIT_LOG_FILE)
        except FileNotFoundError:
            audit_df = pd.DataFrame(columns=['timestamp', 'admin_user_id', 'admin_email', 
                                           'action', 'target_user_email', 'details', 'ip_address'])
        
        # Append new entry
        new_entry_df = pd.DataFrame([log_entry])
        audit_df = pd.concat([audit_df, new_entry_df], ignore_index=True)
        
        # Save audit log
        audit_df.to_csv(AUDIT_LOG_FILE, index=False)
        
    except Exception as e:
        print(f"Error logging admin action: {e}")

def populate_audit_logs_from_face_data():
    """Populate audit logs with face recognition check-in/check-out data"""
    try:
        # Load face log data
        face_log_file = 'logs/face_log.csv'
        if not os.path.exists(face_log_file):
            return False, "Face log file not found"
        
        face_df = pd.read_csv(face_log_file)
        if face_df.empty:
            return False, "No face log data found"
        
        # Parse datetime columns with flexible format
        face_df['check_in'] = pd.to_datetime(face_df['check_in'], format='mixed', errors='coerce')
        face_df['check_out'] = pd.to_datetime(face_df['check_out'], format='mixed', errors='coerce')
        
        # Load existing audit log or create new one
        try:
            audit_df = pd.read_csv(AUDIT_LOG_FILE)
        except FileNotFoundError:
            audit_df = pd.DataFrame(columns=['timestamp', 'admin_user_id', 'admin_email', 
                                           'action', 'target_user_email', 'details', 'ip_address'])
        
        # Create audit entries for each face log entry
        new_entries = []
        
        for _, row in face_df.iterrows():
            tutor_id = str(row['tutor_id'])
            tutor_name = row['tutor_name']
            check_in = row['check_in']
            check_out = row['check_out'] if pd.notna(row['check_out']) else None
            shift_hours = row['shift_hours'] if pd.notna(row['shift_hours']) else 0
            
            # Create check-in entry
            check_in_entry = {
                'timestamp': check_in,
                'admin_user_id': f'SYSTEM_FACE_RECOGNITION',
                'admin_email': 'system@facerecognition.local',
                'action': 'TUTOR_CHECK_IN',
                'target_user_email': f'{tutor_name} (ID: {tutor_id})',
                'details': f'Tutor checked in - Duration: {shift_hours}h',
                'ip_address': 'FACE_RECOGNITION_SYSTEM'
            }
            new_entries.append(check_in_entry)
            
            # Create check-out entry if available
            if check_out:
                check_out_entry = {
                    'timestamp': check_out,
                    'admin_user_id': f'SYSTEM_FACE_RECOGNITION',
                    'admin_email': 'system@facerecognition.local',
                    'action': 'TUTOR_CHECK_OUT',
                    'target_user_email': f'{tutor_name} (ID: {tutor_id})',
                    'details': f'Tutor checked out - Total hours: {shift_hours}h',
                    'ip_address': 'FACE_RECOGNITION_SYSTEM'
                }
                new_entries.append(check_out_entry)
        
        # Convert to DataFrame and combine with existing audit logs
        if new_entries:
            new_entries_df = pd.DataFrame(new_entries)
            
            # Remove duplicates by checking if similar entries already exist
            # (to avoid re-adding the same data if function is called multiple times)
            if not audit_df.empty:
                # Check for existing face recognition entries
                existing_face_entries = audit_df[
                    audit_df['admin_user_id'] == 'SYSTEM_FACE_RECOGNITION'
                ]
                if not existing_face_entries.empty:
                    # Only add entries that don't already exist
                    existing_timestamps = set(existing_face_entries['timestamp'].astype(str))
                    new_entries_df = new_entries_df[
                        ~new_entries_df['timestamp'].astype(str).isin(existing_timestamps)
                    ]
            
            if not new_entries_df.empty:
                # Combine and sort
                audit_df = pd.concat([audit_df, new_entries_df], ignore_index=True)
                audit_df['timestamp'] = pd.to_datetime(audit_df['timestamp'])
                audit_df = audit_df.sort_values('timestamp', ascending=False)
                
                # Create logs directory if it doesn't exist
                os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
                
                # Save updated audit log
                audit_df.to_csv(AUDIT_LOG_FILE, index=False)
                
                return True, f"Added {len(new_entries_df)} new audit log entries from face recognition data"
            else:
                return True, "All face recognition entries already exist in audit logs"
        else:
            return False, "No valid face log entries to process"
            
    except Exception as e:
        return False, f"Error populating audit logs: {str(e)}"

def log_tutor_activity(tutor_id, tutor_name, action, timestamp, shift_hours=None):
    """Log individual tutor activity to audit logs"""
    try:
        details = ""
        if action == "CHECK_IN":
            details = f"Tutor checked in - Duration: {shift_hours}h" if shift_hours else "Tutor checked in"
            action = "TUTOR_CHECK_IN"
        elif action == "CHECK_OUT":
            details = f"Tutor checked out - Total hours: {shift_hours}h" if shift_hours else "Tutor checked out"
            action = "TUTOR_CHECK_OUT"
        
        log_entry = {
            'timestamp': timestamp,
            'admin_user_id': 'SYSTEM_FACE_RECOGNITION',
            'admin_email': 'system@facerecognition.local',
            'action': action,
            'target_user_email': f'{tutor_name} (ID: {tutor_id})',
            'details': details,
            'ip_address': 'FACE_RECOGNITION_SYSTEM'
        }
        
        # Load existing audit log or create new one
        try:
            audit_df = pd.read_csv(AUDIT_LOG_FILE)
        except FileNotFoundError:
            audit_df = pd.DataFrame(columns=['timestamp', 'admin_user_id', 'admin_email', 
                                           'action', 'target_user_email', 'details', 'ip_address'])
        
        # Add new entry
        new_entry_df = pd.DataFrame([log_entry])
        audit_df = pd.concat([audit_df, new_entry_df], ignore_index=True)
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
        
        # Save audit log
        audit_df.to_csv(AUDIT_LOG_FILE, index=False)
        
        return True
        
    except Exception as e:
        print(f"Error logging tutor activity: {e}")
        return False

def get_audit_logs():
    """Get all audit logs (admin only function)"""
    try:
        audit_df = pd.read_csv(AUDIT_LOG_FILE)
        audit_df['timestamp'] = pd.to_datetime(audit_df['timestamp'])
        return audit_df.sort_values('timestamp', ascending=False)
    except FileNotFoundError:
        return pd.DataFrame(columns=['timestamp', 'admin_user_id', 'admin_email', 
                                   'action', 'target_user_email', 'details', 'ip_address'])
    except Exception as e:
        print(f"Error fetching audit logs: {e}")
        return pd.DataFrame()