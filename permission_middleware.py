"""
Permission Middleware for enhanced route protection and data access control
"""

import logging
from functools import wraps
from typing import Dict, List, Optional, Callable, Any
from flask import request, jsonify, session, g
from permissions import Permission, PermissionManager, get_data_access_scope, filter_data_by_permissions
from app.auth.service import get_current_user, get_user_role, get_user_tutor_id, log_admin_action

logger = logging.getLogger(__name__)

class PermissionContext:
    """Context manager for permission-related data"""
    
    def __init__(self):
        self.user = None
        self.role = None
        self.tutor_id = None
        self.permissions = set()
        self.data_scope = "none"
        self.can_modify_users = False
        self.can_export = False
        self.can_manage_system = False
    
    def load_user_context(self):
        """Load current user context and permissions"""
        self.user = get_current_user()
        if self.user:
            self.role = get_user_role()
            self.tutor_id = get_user_tutor_id()
            self.permissions = PermissionManager.get_user_permissions(self.role)
            self.data_scope = get_data_access_scope(self.role)
            self.can_modify_users = PermissionManager.has_any_permission(self.role, [
                Permission.CREATE_USERS,
                Permission.EDIT_USERS,
                Permission.DELETE_USERS,
                Permission.CHANGE_USER_ROLES
            ])
            self.can_export = PermissionManager.has_permission(self.role, Permission.EXPORT_DATA)
            self.can_manage_system = PermissionManager.has_permission(self.role, Permission.MANAGE_SYSTEM_SETTINGS)

def permission_context(f: Callable) -> Callable:
    """Decorator to inject permission context into route handlers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        context = PermissionContext()
        context.load_user_context()
        g.permission_context = context
        return f(*args, **kwargs)
    return decorated_function

def require_data_access(required_scope: str = "own"):
    """Decorator to require specific data access level"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            context = getattr(g, 'permission_context', None)
            if not context:
                context = PermissionContext()
                context.load_user_context()
                g.permission_context = context
            
            scope_levels = {"none": 0, "own": 1, "team": 2, "all": 3}
            user_scope_level = scope_levels.get(context.data_scope, 0)
            required_scope_level = scope_levels.get(required_scope, 0)
            
            if user_scope_level < required_scope_level:
                if request.is_json:
                    return jsonify({
                        "error": {
                            "message": "Insufficient data access permissions",
                            "code": "INSUFFICIENT_DATA_ACCESS",
                            "details": {
                                "required_scope": required_scope,
                                "user_scope": context.data_scope
                            }
                        }
                    }), 403
                return jsonify({"error": "You don't have permission to access this data"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def api_permission_required(permission: Permission):
    """API-specific permission decorator with enhanced error responses"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            context = getattr(g, 'permission_context', None)
            if not context:
                context = PermissionContext()
                context.load_user_context()
                g.permission_context = context
            
            if not context.user:
                return jsonify({
                    "error": {
                        "message": "Authentication required",
                        "code": "AUTH_REQUIRED",
                        "details": {"endpoint": request.endpoint}
                    }
                }), 401
            
            if permission not in context.permissions:
                return jsonify({
                    "error": {
                        "message": "Insufficient permissions",
                        "code": "FORBIDDEN",
                        "details": {
                            "required_permission": permission.value,
                            "user_role": context.role,
                            "available_permissions": [p.value for p in context.permissions]
                        }
                    }
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def conditional_permission(permission: Permission, fallback_response: Any = None):
    """Decorator that checks permission but allows fallback response instead of error"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            context = getattr(g, 'permission_context', None)
            if not context:
                context = PermissionContext()
                context.load_user_context()
                g.permission_context = context
            
            if not context.user or permission not in context.permissions:
                if fallback_response is not None:
                    return fallback_response
                return jsonify({"error": "Permission denied"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def data_filter_required():
    """Decorator to automatically filter data based on user permissions"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            context = getattr(g, 'permission_context', None)
            if not context:
                context = PermissionContext()
                context.load_user_context()
                g.permission_context = context
            
            # Store original function
            original_func = f
            
            # Create wrapper that filters data
            def wrapper(*args, **kwargs):
                result = original_func(*args, **kwargs)
                
                # If result is a dataframe, filter it
                if hasattr(result, 'iloc'):  # pandas DataFrame
                    return filter_data_by_permissions(
                        result, 
                        context.role, 
                        context.tutor_id, 
                        context.user.get('email') if context.user else None
                    )
                
                # If result is a list of dicts (JSON response)
                if isinstance(result, list) and result and isinstance(result[0], dict):
                    # Apply filtering logic based on data scope
                    if context.data_scope == "own" and context.tutor_id:
                        return [item for item in result if str(item.get('tutor_id', '')) == str(context.tutor_id)]
                    elif context.data_scope == "team":
                        # Implement team filtering logic here
                        pass
                    elif context.data_scope == "none":
                        return []
                
                return result
            
            return wrapper(*args, **kwargs)
        return decorated_function
    return decorator

def audit_permission_action(action: str):
    """Decorator to audit permission-related actions"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            context = getattr(g, 'permission_context', None)
            if not context:
                context = PermissionContext()
                context.load_user_context()
                g.permission_context = context
            
            # Log the action
            try:
                if context.user:
                    log_admin_action(
                        action=f"PERMISSION_{action}",
                        target_user_email=context.user.get('email'),
                        details=f"Action: {action}, Role: {context.role}, Endpoint: {request.endpoint}"
                    )
            except Exception as e:
                logger.warning(f"Failed to log permission action: {e}")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_user_modification(target_user_email: str) -> bool:
    """Validate if current user can modify target user"""
    context = getattr(g, 'permission_context', None)
    if not context:
        context = PermissionContext()
        context.load_user_context()
        g.permission_context = context
    
    if not context.user:
        return False
    
    current_email = context.user.get('email', '')
    
    # Users can always modify themselves
    if current_email == target_user_email:
        return True
    
    # Check if current role can modify target role
    from permissions import can_modify_user
    return can_modify_user(target_user_email)

def get_user_capabilities() -> Dict[str, Any]:
    """Get current user's capabilities for frontend"""
    context = getattr(g, 'permission_context', None)
    if not context:
        context = PermissionContext()
        context.load_user_context()
        g.permission_context = context
    
    if not context.user:
        return {}
    
    return {
        "role": context.role,
        "data_scope": context.data_scope,
        "permissions": [p.value for p in context.permissions],
        "capabilities": {
            "can_manage_users": context.can_modify_users,
            "can_export_data": context.can_export,
            "can_manage_system": context.can_manage_system,
            "can_view_analytics": PermissionManager.has_any_permission(context.role, [
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_ADVANCED_ANALYTICS
            ]),
            "can_generate_reports": PermissionManager.has_permission(context.role, Permission.GENERATE_REPORTS),
            "can_view_audit_logs": PermissionManager.has_permission(context.role, Permission.VIEW_AUDIT_LOGS),
        }
    }

# Middleware for automatic permission context injection
def init_permission_middleware(app):
    """Initialize permission middleware for the Flask app"""
    
    @app.before_request
    def load_permission_context():
        """Load permission context for every request"""
        context = PermissionContext()
        context.load_user_context()
        g.permission_context = context
    
    @app.after_request
    def add_permission_headers(response):
        """Add permission-related headers to responses"""
        context = getattr(g, 'permission_context', None)
        if context and context.user:
            response.headers['X-User-Role'] = context.role or 'unknown'
            response.headers['X-Data-Scope'] = context.data_scope
        return response
