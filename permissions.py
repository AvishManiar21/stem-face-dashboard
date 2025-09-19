"""
Enhanced Permission System for Tutor Face Recognition Dashboard
Provides granular permission management with capabilities and better security
"""

import logging
from enum import Enum
from functools import wraps
from typing import Dict, List, Set, Optional, Callable, Any
from flask import session, request, jsonify, redirect, url_for, flash
from auth import get_current_user, get_user_role, error_response

logger = logging.getLogger(__name__)

class Permission(Enum):
    """Specific permission capabilities"""
    # User Management
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    EDIT_USERS = "edit_users"
    DELETE_USERS = "delete_users"
    CHANGE_USER_ROLES = "change_user_roles"
    ACTIVATE_DEACTIVATE_USERS = "activate_deactivate_users"
    
    # Data Access
    VIEW_ALL_DATA = "view_all_data"
    VIEW_OWN_DATA = "view_own_data"
    VIEW_TEAM_DATA = "view_team_data"
    EXPORT_DATA = "export_data"
    
    # Analytics & Reports
    VIEW_ANALYTICS = "view_analytics"
    VIEW_ADVANCED_ANALYTICS = "view_advanced_analytics"
    GENERATE_REPORTS = "generate_reports"
    
    # System Administration
    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_SHIFTS = "manage_shifts"
    
    # Face Recognition
    MANAGE_FACE_RECOGNITION = "manage_face_recognition"
    VIEW_FACE_LOGS = "view_face_logs"
    MANAGE_FACE_DATABASE = "manage_face_database"

class Role(Enum):
    """User roles with hierarchical levels"""
    TUTOR = "tutor"
    LEAD_TUTOR = "lead_tutor"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

# Role hierarchy levels (higher number = more permissions)
ROLE_LEVELS = {
    Role.TUTOR: 1,
    Role.LEAD_TUTOR: 2,
    Role.MANAGER: 3,
    Role.ADMIN: 4,
    Role.SUPER_ADMIN: 5
}

# Permission mappings for each role
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.TUTOR: {
        Permission.VIEW_OWN_DATA,
        Permission.VIEW_FACE_LOGS,
    },
    
    Role.LEAD_TUTOR: {
        Permission.VIEW_OWN_DATA,
        Permission.VIEW_TEAM_DATA,
        Permission.VIEW_FACE_LOGS,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_USERS,  # Read-only
        Permission.MANAGE_SHIFTS,
    },
    
    Role.MANAGER: {
        Permission.VIEW_ALL_DATA,
        Permission.VIEW_OWN_DATA,
        Permission.VIEW_TEAM_DATA,
        Permission.VIEW_FACE_LOGS,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_ADVANCED_ANALYTICS,
        Permission.GENERATE_REPORTS,
        Permission.EXPORT_DATA,
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.EDIT_USERS,
        Permission.CHANGE_USER_ROLES,
        Permission.ACTIVATE_DEACTIVATE_USERS,
        Permission.MANAGE_SHIFTS,
        Permission.VIEW_AUDIT_LOGS,
    },
    
    Role.ADMIN: {
        Permission.VIEW_ALL_DATA,
        Permission.VIEW_OWN_DATA,
        Permission.VIEW_TEAM_DATA,
        Permission.VIEW_FACE_LOGS,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_ADVANCED_ANALYTICS,
        Permission.GENERATE_REPORTS,
        Permission.EXPORT_DATA,
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.EDIT_USERS,
        Permission.DELETE_USERS,
        Permission.CHANGE_USER_ROLES,
        Permission.ACTIVATE_DEACTIVATE_USERS,
        Permission.MANAGE_SHIFTS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_SYSTEM_SETTINGS,
        Permission.MANAGE_FACE_RECOGNITION,
        Permission.MANAGE_FACE_DATABASE,
    },
    
    Role.SUPER_ADMIN: {
        # Super admin has all permissions
        *[p for p in Permission]
    }
}

class PermissionManager:
    """Centralized permission management"""
    
    @staticmethod
    def get_user_permissions(user_role: str) -> Set[Permission]:
        """Get all permissions for a user role"""
        try:
            role = Role(user_role.lower())
            return ROLE_PERMISSIONS.get(role, set())
        except ValueError:
            logger.warning(f"Unknown role: {user_role}")
            return set()
    
    @staticmethod
    def has_permission(user_role: str, permission: Permission) -> bool:
        """Check if user role has specific permission"""
        user_permissions = PermissionManager.get_user_permissions(user_role)
        return permission in user_permissions
    
    @staticmethod
    def has_any_permission(user_role: str, permissions: List[Permission]) -> bool:
        """Check if user role has any of the specified permissions"""
        user_permissions = PermissionManager.get_user_permissions(user_role)
        return any(perm in user_permissions for perm in permissions)
    
    @staticmethod
    def has_all_permissions(user_role: str, permissions: List[Permission]) -> bool:
        """Check if user role has all of the specified permissions"""
        user_permissions = PermissionManager.get_user_permissions(user_role)
        return all(perm in user_permissions for perm in permissions)
    
    @staticmethod
    def can_access_role(target_role: str, current_role: str) -> bool:
        """Check if current role can access/modify target role"""
        try:
            current_level = ROLE_LEVELS.get(Role(current_role.lower()), 0)
            target_level = ROLE_LEVELS.get(Role(target_role.lower()), 999)
            return current_level > target_level
        except ValueError:
            return False

def permission_required(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.is_json:
                    return error_response("Authentication required", status_code=401, code="AUTH_REQUIRED")
                return redirect(url_for('login'))
            
            user_role = get_user_role()
            if not PermissionManager.has_permission(user_role, permission):
                if request.is_json:
                    return error_response(
                        "Insufficient permissions", 
                        status_code=403, 
                        code="FORBIDDEN", 
                        details={
                            "required_permission": permission.value,
                            "user_role": user_role
                        }
                    )
                flash(f'You do not have permission to {permission.value.replace("_", " ")}.', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permissions_required(permissions: List[Permission], require_all: bool = True):
    """Decorator to require multiple permissions"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.is_json:
                    return error_response("Authentication required", status_code=401, code="AUTH_REQUIRED")
                return redirect(url_for('login'))
            
            user_role = get_user_role()
            has_permission = (PermissionManager.has_all_permissions if require_all 
                            else PermissionManager.has_any_permission)(user_role, permissions)
            
            if not has_permission:
                if request.is_json:
                    return error_response(
                        "Insufficient permissions", 
                        status_code=403, 
                        code="FORBIDDEN", 
                        details={
                            "required_permissions": [p.value for p in permissions],
                            "require_all": require_all,
                            "user_role": user_role
                        }
                    )
                flash('You do not have sufficient permissions for this action.', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_required(required_role: Role):
    """Decorator to require specific role or higher"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.is_json:
                    return error_response("Authentication required", status_code=401, code="AUTH_REQUIRED")
                return redirect(url_for('login'))
            
            user_role = get_user_role()
            user_level = ROLE_LEVELS.get(Role(user_role.lower()), 0)
            required_level = ROLE_LEVELS.get(required_role, 0)
            
            if user_level < required_level:
                if request.is_json:
                    return error_response(
                        "Insufficient permissions", 
                        status_code=403, 
                        code="FORBIDDEN", 
                        details={
                            "required_role": required_role.value,
                            "user_role": user_role
                        }
                    )
                flash(f'You must be a {required_role.value.replace("_", " ")} or higher to access this page.', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def can_modify_user(target_user_email: str) -> bool:
    """Check if current user can modify target user"""
    current_user = get_current_user()
    if not current_user:
        return False
    
    current_role = get_user_role()
    current_email = current_user.get('email', '')
    
    # Users can always modify themselves (for profile updates)
    if current_email == target_user_email:
        return True
    
    # Get target user's role
    target_role = get_user_role(target_user_email)
    
    # Check if current role can modify target role
    return PermissionManager.can_access_role(target_role, current_role)

def get_data_access_scope(user_role: str) -> str:
    """Get data access scope for user role"""
    if PermissionManager.has_permission(user_role, Permission.VIEW_ALL_DATA):
        return "all"
    elif PermissionManager.has_permission(user_role, Permission.VIEW_TEAM_DATA):
        return "team"
    elif PermissionManager.has_permission(user_role, Permission.VIEW_OWN_DATA):
        return "own"
    else:
        return "none"

def filter_data_by_permissions(df, user_role: str, user_tutor_id: str = None, user_email: str = None):
    """Enhanced data filtering based on permissions"""
    scope = get_data_access_scope(user_role)
    
    if scope == "all":
        return df
    elif scope == "team":
        # Lead tutors can see team data - implement team logic here
        # For now, return all data (can be refined based on team structure)
        return df
    elif scope == "own":
        # Filter to user's own data
        if user_tutor_id and 'tutor_id' in df.columns:
            return df[df['tutor_id'].astype(str) == str(user_tutor_id)]
        elif user_email and 'tutor_name' in df.columns:
            # Fallback to name matching
            current_user = get_current_user()
            if current_user and 'user_metadata' in current_user:
                full_name = current_user['user_metadata'].get('full_name')
                if full_name:
                    return df[df['tutor_name'].astype(str).str.strip().str.lower() == full_name.strip().lower()]
        return df.iloc[0:0]  # Empty dataframe
    else:
        return df.iloc[0:0]  # No access

def log_permission_action(action: str, target: str = None, details: str = None):
    """Log permission-related actions for audit trail"""
    try:
        from analytics import analytics as _analytics
        if _analytics:
            _analytics.log_admin_action(
                action=f"PERMISSION_{action}",
                target_user_email=target,
                details=details
            )
    except Exception as e:
        logger.warning(f"Failed to log permission action: {e}")

# Convenience functions for common permission checks
def can_manage_users(user_role: str) -> bool:
    """Check if user can manage other users"""
    return PermissionManager.has_any_permission(user_role, [
        Permission.CREATE_USERS,
        Permission.EDIT_USERS,
        Permission.DELETE_USERS,
        Permission.CHANGE_USER_ROLES
    ])

def can_view_analytics(user_role: str) -> bool:
    """Check if user can view analytics"""
    return PermissionManager.has_any_permission(user_role, [
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_ADVANCED_ANALYTICS
    ])

def can_export_data(user_role: str) -> bool:
    """Check if user can export data"""
    return PermissionManager.has_permission(user_role, Permission.EXPORT_DATA)

def can_manage_system(user_role: str) -> bool:
    """Check if user can manage system settings"""
    return PermissionManager.has_permission(user_role, Permission.MANAGE_SYSTEM_SETTINGS)
