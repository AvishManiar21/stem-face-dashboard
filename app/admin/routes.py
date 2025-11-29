"""Admin blueprint"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session

admin_bp = Blueprint('admin', __name__)

from app.auth.service import get_current_user, get_user_role as service_get_user_role

def get_user_role(user=None):
    """Get user's role"""
    if not user:
        user = get_current_user()
    if not user:
        return None
    
    # Try different ways to get role
    role = user.get('role')
    if not role:
        role = user.get('user_metadata', {}).get('role')
    if not role and 'email' in user:
        # Try to get from auth module
        try:
            role = service_get_user_role(user.get('email'))
        except:
            pass
    return role

def require_admin_access():
    """Check if user is authenticated and has admin access
    
    Access is granted if:
    1. User has admin/system_admin/manager role, OR
    2. User email/user_id is in the allowed feature toggle users list
    """
    import os
    user = get_current_user()
    if not user:
        # Try to get login route name
        try:
            return None, redirect('/login')
        except:
            return None, redirect(url_for('login'))
    
    # Get user identifier (email or user_id)
    user_email = user.get('email', '')
    user_id = user.get('id') or user.get('user_id', '')
    
    # Check if user has admin role
    user_role = get_user_role(user)
    allowed_roles = ['admin', 'system_admin', 'manager']
    
    if user_role not in allowed_roles:
        return None, None  # Will return 403
    
    return user, None

@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard with feature toggles - for authorized users only"""
    user, redirect_response = require_admin_access()
    if redirect_response:
        flash('Please login to access the admin dashboard', 'warning')
        return redirect_response
    
    if not user:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect('/login'), 403
    
    try:
        # Get user info for display
        user_email = user.get('email', 'Unknown')
        user_name = user.get('full_name') or user.get('user_metadata', {}).get('full_name', user_email)
        user_role = get_user_role(user) or 'Unknown'
        
        return render_template('admin/dashboard.html', 
                             current_user={
                                 'email': user_email,
                                 'name': user_name,
                                 'role': user_role
                             })
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return render_template('admin/dashboard.html', 
                             current_user={'email': 'Unknown', 'name': 'Unknown', 'role': 'Unknown'})



@admin_bp.route('/api/current-user')
def api_current_user():
    """Get current user info for navbar display"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_email = user.get('email', 'Unknown')
    user_name = user.get('full_name') or user.get('user_metadata', {}).get('full_name', user_email.split('@')[0])
    user_role = get_user_role(user) or 'user'
    
    return jsonify({
        'email': user_email,
        'name': user_name,
        'role': user_role
    })

@admin_bp.route('/api/dashboard-stats')
def api_dashboard_stats():
    """Get dashboard statistics"""
    user, redirect_response = require_admin_access()
    if redirect_response or not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import pandas as pd
        import os
        from datetime import datetime
        
        stats = {
            'total_tutors': 0,
            'active_courses': 0,
            'appointments_today': 0,
            'total_users': 0
        }
        
        # Count tutors
        tutors_file = 'data/core/tutors.csv'
        if os.path.exists(tutors_file):
            try:
                df = pd.read_csv(tutors_file)
                stats['total_tutors'] = len(df)
            except:
                pass
        
        # Count courses
        courses_file = 'data/core/courses.csv'
        if os.path.exists(courses_file):
            try:
                df = pd.read_csv(courses_file)
                stats['active_courses'] = len(df)
            except:
                pass
        
        # Count today's appointments
        appointments_file = 'data/core/appointments.csv'
        if os.path.exists(appointments_file):
            try:
                df = pd.read_csv(appointments_file)
                if not df.empty and 'appointment_date' in df.columns:
                    today = datetime.now().strftime('%Y-%m-%d')
                    stats['appointments_today'] = len(df[df['appointment_date'] == today])
            except:
                pass
        
        # Count users
        users_file = 'data/core/users.csv'
        if os.path.exists(users_file):
            try:
                df = pd.read_csv(users_file)
                stats['total_users'] = len(df)
            except:
                pass
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
