"""Auth blueprint"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.auth.service import authenticate_user, get_current_user, logout_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page and form submission"""
    # If already logged in and authorized, redirect to admin dashboard
    user = get_current_user()
    if user:
        user_role = user.get('role', '')
        # Check if user has admin access
        if user_role in ['admin', 'system_admin', 'manager']:
            return redirect(url_for('admin.dashboard'))
        # Check if user is in allowed list
        import os
        allowed_users_env = os.getenv('FEATURE_TOGGLE_ALLOWED_USERS', '')
        allowed_users = [u.strip().lower() for u in allowed_users_env.split(',') if u.strip()]
        user_email = user.get('email', '').lower()
        user_id = str(user.get('user_id') or user.get('id', '')).lower()
        if allowed_users and (user_email in allowed_users or user_id in allowed_users):
            return redirect(url_for('admin.dashboard'))
        
        # Default redirect for logged in users who are not admins
        return redirect('/')

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        success, message = authenticate_user(email, password)
        if success:
            # Store user in session (already handled by authenticate_user)
            # Check if user should be redirected to admin dashboard
            user = get_current_user()
            if user:
                user_role = user.get('role', '')
                # Check if user has admin access
                if user_role in ['admin', 'system_admin', 'manager']:
                    return redirect(url_for('admin.dashboard'))
                # Check if user is in allowed list
                import os
                allowed_users_env = os.getenv('FEATURE_TOGGLE_ALLOWED_USERS', '')
                allowed_users = [u.strip().lower() for u in allowed_users_env.split(',') if u.strip()]
                user_email = user.get('email', '').lower()
                user_id = str(user.get('user_id') or user.get('id', '')).lower()
                if allowed_users and (user_email in allowed_users or user_id in allowed_users):
                    return redirect(url_for('admin.dashboard'))
            # Default redirect
            return redirect('/')
        # On failure, re-render login page with inline error and preserved email
        flash(message or 'Invalid credentials', 'error')
        return render_template('login.html', default_email=email), 400
    
    # GET request
    return render_template('login.html', default_email=request.args.get('email', ''))

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    logout_user()
    return redirect(url_for('auth.login'))
