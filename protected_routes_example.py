"""
Example of how to protect dashboard routes using group permissions
"""

from flask import Blueprint, render_template, jsonify, request
from functools import wraps
from auth import get_current_user, get_user_role
from group_helpers import (
    user_has_group_permission, 
    get_user_all_permissions, 
    can_user_access_group,
    group_permission_required
)
from permissions import Permission as PermissionEnum, PermissionManager

# Create blueprint for protected routes
protected_bp = Blueprint('protected', __name__)

# Example 1: Basic route protection using group permissions
@protected_bp.route('/admin/dashboard')
@group_permission_required('view_all_data')
def admin_dashboard():
    """Admin dashboard - requires view_all_data permission through groups or role"""
    user = get_current_user()
    user_id = user.get('id') or user.get('user_id')
    
    # Get user's permissions for display
    user_permissions = get_user_all_permissions(user_id)
    
    return render_template('admin_dashboard.html', 
                         user=user, 
                         permissions=user_permissions)

# Example 2: Route that checks specific group membership
@protected_bp.route('/team/analytics')
def team_analytics():
    """Team analytics - requires team group membership"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = user.get('id') or user.get('user_id')
    
    # Check if user is in a team group
    from group_helpers import get_user_groups
    user_groups = get_user_groups(user_id)
    
    # Find team groups (you can define your own logic for identifying team groups)
    team_groups = [group for group in user_groups if 'team' in group['name'].lower()]
    
    if not team_groups:
        return jsonify({'error': 'You must be a member of a team group to access this page'}), 403
    
    return render_template('team_analytics.html', 
                         user=user, 
                         team_groups=team_groups)

# Example 3: Route with conditional access based on group permissions
@protected_bp.route('/reports')
def reports():
    """Reports page - different access levels based on permissions"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = user.get('id') or user.get('user_id')
    user_permissions = get_user_all_permissions(user_id)
    
    # Determine what reports user can see
    can_view_basic = 'view_analytics' in user_permissions
    can_view_advanced = 'view_advanced_analytics' in user_permissions
    can_export = 'export_data' in user_permissions
    
    return render_template('reports.html',
                         user=user,
                         can_view_basic=can_view_basic,
                         can_view_advanced=can_view_advanced,
                         can_export=can_export)

# Example 4: API endpoint with group-based data filtering
@protected_bp.route('/api/group-data/<int:group_id>')
def get_group_data(group_id):
    """Get data for a specific group - requires group membership"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = user.get('id') or user.get('user_id')
    
    # Check if user can access this group
    if not can_user_access_group(user_id, group_id):
        return jsonify({'error': 'You do not have access to this group'}), 403
    
    # Get group data (implement your data retrieval logic here)
    from models import Group
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    # Return group-specific data
    return jsonify({
        'group': group.to_dict(),
        'message': f'Data for group: {group.name}'
    })

# Example 5: Route that requires both role and group permissions
@protected_bp.route('/advanced/settings')
def advanced_settings():
    """Advanced settings - requires both admin role AND specific group permission"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_role = get_user_role()
    user_id = user.get('id') or user.get('user_id')
    
    # Check role-based permission
    if not PermissionManager.has_permission(user_role, PermissionEnum.MANAGE_SYSTEM_SETTINGS):
        return jsonify({'error': 'Admin role required'}), 403
    
    # Check group-based permission
    user_groups = get_user_groups(user_id)
    has_group_permission = False
    
    for group in user_groups:
        if user_has_group_permission(user_id, group['id'], 'manage_system_settings'):
            has_group_permission = True
            break
    
    if not has_group_permission:
        return jsonify({'error': 'System administrators group membership required'}), 403
    
    return render_template('advanced_settings.html', user=user)

# Example 6: Helper function for checking permissions in templates
def check_user_permission(user_id, permission_name):
    """Helper function to check if user has a specific permission"""
    user_permissions = get_user_all_permissions(user_id)
    return permission_name in user_permissions

def check_user_group_membership(user_id, group_name):
    """Helper function to check if user is a member of a specific group"""
    user_groups = get_user_groups(user_id)
    return any(group['name'].lower() == group_name.lower() for group in user_groups)

# Example 7: Middleware for adding permission context to all requests
def add_permission_context():
    """Add permission context to Flask's g object for use in templates"""
    from flask import g
    
    user = get_current_user()
    if user:
        user_id = user.get('id') or user.get('user_id')
        if user_id:
            g.user_permissions = get_user_all_permissions(user_id)
            g.user_groups = get_user_groups(user_id)
        else:
            g.user_permissions = []
            g.user_groups = []
    else:
        g.user_permissions = []
        g.user_groups = []

# Example 8: Custom decorator for group-specific permissions
def group_lead_required(f):
    """Decorator to require group lead permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        user_id = user.get('id') or user.get('user_id')
        user_groups = get_user_groups(user_id)
        
        # Check if user is a lead of any group
        is_group_lead = any(group.get('lead_user_id') == user_id for group in user_groups)
        
        # Or check if user is admin/manager
        user_role = get_user_role()
        is_admin = user_role in ['admin', 'manager']
        
        if not (is_group_lead or is_admin):
            return jsonify({'error': 'Group lead permissions required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@protected_bp.route('/group-management')
@group_lead_required
def group_management():
    """Group management page - requires group lead permissions"""
    user = get_current_user()
    return render_template('group_management.html', user=user)
