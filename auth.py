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
from auth_utils import USERS_FILE, hash_password as legacy_hash_password
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check if Supabase environment variables are set
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Initialize Supabase client only if environment variables are available
supabase = None
if supabase_url and supabase_key:
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        supabase = None
else:
    logger.warning("Supabase environment variables not set. Running in demo mode with local authentication.")

# Role hierarchy for access control
ROLE_HIERARCHY = {
    'tutor': 1,
    'lead_tutor': 2, 
    'manager': 3,
    'admin': 3  # Admin same level as manager
}

# Audit log file
AUDIT_LOG_FILE = 'logs/audit_log.csv'

DEMO_USERS = {}

def get_current_user():
    """Get current authenticated user from session"""
    if 'user' in session:
        return session['user']
    return None

def get_user_role(email=None):
    """Get user's role - current user if no email provided, or specific user by email"""
    if not supabase:
        # Demo mode - use local users
        if email:
            if email in DEMO_USERS:
                return DEMO_USERS[email]['user_metadata'].get('role', 'tutor')
        else:
            user = get_current_user()
            if user and 'user_metadata' in user:
                return user['user_metadata'].get('role', 'tutor')
        return 'tutor'
    
    # Supabase mode
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
    Hybrid authentication - tries Supabase Auth first, then custom users table, then demo users, then local CSV users
    """
    if not email or not password:
        return False, "Email and password are required"
    
    # First try Supabase Auth if available
    if supabase:
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
    
    # If Supabase is not available, try local CSV users
    import pandas as pd
    import os
    if os.path.exists(USERS_FILE):
        df = pd.read_csv(USERS_FILE)
        user_row = df[df['email'] == email]
        if not user_row.empty:
            user = user_row.iloc[0]
            if not user.get('active', True):
                return False, "User is not active"
            stored_hash = user.get('password_hash', '')
            if stored_hash:
                # Support both SHA-256 (64 hex) and legacy MD5 (32 hex)
                try:
                    if isinstance(stored_hash, str) and len(stored_hash.strip()) == 32:
                        candidate = hashlib.md5(password.encode()).hexdigest()
                    else:
                        candidate = legacy_hash_password(password)
                except Exception:
                    candidate = legacy_hash_password(password)
                if candidate == stored_hash:
                    session['user'] = {
                        'id': user.get('user_id'),
                        'email': user.get('email'),
                        'user_metadata': {
                            'role': user.get('role', 'tutor'),
                            'full_name': user.get('full_name', ''),
                            'tutor_id': user.get('user_id')
                        }
                    }
                    logger.info(f"User {email} authenticated via local CSV users")
                    return True, "Login successful"
            return False, "Invalid email or password"
    
    return False, "Invalid email or password"

def logout_user():
    """Logout current user"""
    try:
        # Sign out from Supabase if available
        if supabase:
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
    
    # If Supabase is not available, return demo mode message
    if not supabase:
        return False, "User registration is not available in demo mode. Please set up Supabase environment variables for full functionality."
    
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
    # If Supabase is not available, return demo mode message
    if not supabase:
        return False, "User role updates are not available in demo mode. Please set up Supabase environment variables for full functionality."
    
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