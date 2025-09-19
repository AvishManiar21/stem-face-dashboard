"""
Helper functions for user grouping and permission control
"""

import logging
from typing import List, Dict, Optional, Set
from models import db, Group, GroupMember, Permission, User
from auth import get_current_user, get_user_role
from permissions import Permission as PermissionEnum, PermissionManager

logger = logging.getLogger(__name__)

def user_has_group_permission(user_id: int, group_id: int, permission_name: str) -> bool:
    """
    Check if a user has a specific permission in a group
    
    Args:
        user_id: ID of the user
        group_id: ID of the group
        permission_name: Name of the permission to check
    
    Returns:
        bool: True if user has the permission, False otherwise
    """
    try:
        # Get user
        user = User.query.get(user_id)
        if not user:
            return False
        
        # Check if user is a member of the group
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=user_id,
            active=True
        ).first()
        
        if not membership:
            return False
        
        # Get group
        group = Group.query.get(group_id)
        if not group:
            return False
        
        # Check if group has the permission
        permission = Permission.query.filter_by(name=permission_name, active=True).first()
        if not permission:
            return False
        
        return permission in group.permissions
        
    except Exception as e:
        logger.error(f"Error checking group permission: {e}")
        return False

def get_user_groups(user_id: int) -> List[Dict]:
    """Get all groups a user belongs to"""
    try:
        user = User.query.get(user_id)
        if not user:
            return []
        
        return [group.to_dict() for group in user.get_groups()]
    except Exception as e:
        logger.error(f"Error getting user groups: {e}")
        return []

def get_user_group_permissions(user_id: int) -> List[str]:
    """Get all permissions a user has through group memberships"""
    try:
        user = User.query.get(user_id)
        if not user:
            return []
        
        permissions = set()
        for group in user.get_groups():
            for permission in group.permissions:
                if permission.active:
                    permissions.add(permission.name)
        
        return list(permissions)
    except Exception as e:
        logger.error(f"Error getting user group permissions: {e}")
        return []

def get_user_all_permissions(user_id: int) -> Set[str]:
    """
    Get all permissions a user has (role-based + group-based)
    
    Args:
        user_id: ID of the user
    
    Returns:
        Set of permission names
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return set()
        
        # Get role-based permissions
        role_permissions = set()
        if user.role:
            role_perms = PermissionManager.get_user_permissions(user.role)
            role_permissions = {perm.value for perm in role_perms}
        
        # Get group-based permissions
        group_permissions = set(get_user_group_permissions(user_id))
        
        # Combine both sets
        all_permissions = role_permissions.union(group_permissions)
        
        return all_permissions
        
    except Exception as e:
        logger.error(f"Error getting user all permissions: {e}")
        return set()

def can_user_access_group(user_id: int, group_id: int) -> bool:
    """
    Check if a user can access a group (is member or lead)
    
    Args:
        user_id: ID of the user
        group_id: ID of the group
    
    Returns:
        bool: True if user can access the group
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return False
        
        # Check if user is a member of the group
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=user_id,
            active=True
        ).first()
        
        if membership:
            return True
        
        # Check if user is the group lead
        group = Group.query.get(group_id)
        if group and group.lead_user_id == user_id:
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking group access: {e}")
        return False

def can_user_manage_group(user_id: int, group_id: int) -> bool:
    """
    Check if a user can manage a group (is lead or admin/manager)
    
    Args:
        user_id: ID of the user
        group_id: ID of the group
    
    Returns:
        bool: True if user can manage the group
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return False
        
        # Admin and manager can manage all groups
        if user.role in ['admin', 'manager']:
            return True
        
        # Check if user is the group lead
        group = Group.query.get(group_id)
        if group and group.lead_user_id == user_id:
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking group management: {e}")
        return False

def get_group_members_with_permissions(group_id: int) -> List[Dict]:
    """
    Get all members of a group with their permissions
    
    Args:
        group_id: ID of the group
    
    Returns:
        List of member dictionaries with permission info
    """
    try:
        group = Group.query.get(group_id)
        if not group:
            return []
        
        members = []
        for membership in group.members:
            if membership.active:
                member_data = membership.to_dict()
                
                # Get member's role-based permissions
                role_permissions = set()
                if membership.user.role:
                    role_perms = PermissionManager.get_user_permissions(membership.user.role)
                    role_permissions = {perm.value for perm in role_perms}
                
                # Get member's group-based permissions (from this group)
                group_permissions = set()
                for permission in group.permissions:
                    if permission.active:
                        group_permissions.add(permission.name)
                
                # Combine permissions
                all_permissions = role_permissions.union(group_permissions)
                
                member_data['permissions'] = list(all_permissions)
                member_data['role_permissions'] = list(role_permissions)
                member_data['group_permissions'] = list(group_permissions)
                
                members.append(member_data)
        
        return members
        
    except Exception as e:
        logger.error(f"Error getting group members with permissions: {e}")
        return []

def create_default_permissions():
    """Create default permissions if they don't exist"""
    try:
        default_permissions = [
            {
                'name': 'view_users',
                'description': 'View user information',
                'category': 'user_management'
            },
            {
                'name': 'create_users',
                'description': 'Create new users',
                'category': 'user_management'
            },
            {
                'name': 'edit_users',
                'description': 'Edit user information',
                'category': 'user_management'
            },
            {
                'name': 'delete_users',
                'description': 'Delete users',
                'category': 'user_management'
            },
            {
                'name': 'view_all_data',
                'description': 'View all data in the system',
                'category': 'data_access'
            },
            {
                'name': 'view_own_data',
                'description': 'View own data only',
                'category': 'data_access'
            },
            {
                'name': 'view_team_data',
                'description': 'View team data',
                'category': 'data_access'
            },
            {
                'name': 'export_data',
                'description': 'Export data from the system',
                'category': 'data_access'
            },
            {
                'name': 'view_analytics',
                'description': 'View basic analytics',
                'category': 'analytics'
            },
            {
                'name': 'view_advanced_analytics',
                'description': 'View advanced analytics',
                'category': 'analytics'
            },
            {
                'name': 'generate_reports',
                'description': 'Generate reports',
                'category': 'analytics'
            },
            {
                'name': 'manage_system_settings',
                'description': 'Manage system settings',
                'category': 'system'
            },
            {
                'name': 'view_audit_logs',
                'description': 'View audit logs',
                'category': 'system'
            },
            {
                'name': 'manage_shifts',
                'description': 'Manage shifts and schedules',
                'category': 'shifts'
            },
            {
                'name': 'manage_face_recognition',
                'description': 'Manage face recognition system',
                'category': 'face_recognition'
            },
            {
                'name': 'view_face_logs',
                'description': 'View face recognition logs',
                'category': 'face_recognition'
            },
            {
                'name': 'manage_face_database',
                'description': 'Manage face database',
                'category': 'face_recognition'
            }
        ]
        
        for perm_data in default_permissions:
            existing = Permission.query.filter_by(name=perm_data['name']).first()
            if not existing:
                permission = Permission(
                    name=perm_data['name'],
                    description=perm_data['description'],
                    category=perm_data['category']
                )
                db.session.add(permission)
        
        db.session.commit()
        logger.info("Default permissions created successfully")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating default permissions: {e}")

def initialize_group_system():
    """Initialize the group system with default data"""
    try:
        # Create default permissions
        create_default_permissions()
        
        # Create a default admin group if it doesn't exist
        admin_group = Group.query.filter_by(name='Administrators').first()
        if not admin_group:
            # Find an admin user to be the lead
            admin_user = User.query.filter_by(role='admin').first()
            if admin_user:
                admin_group = Group(
                    name='Administrators',
                    description='System administrators group',
                    lead_user_id=admin_user.id
                )
                db.session.add(admin_group)
                db.session.flush()
                
                # Add admin user as member
                admin_member = GroupMember(
                    group_id=admin_group.id,
                    user_id=admin_user.id,
                    role='lead'
                )
                db.session.add(admin_member)
                
                # Assign all permissions to admin group
                all_permissions = Permission.query.filter_by(active=True).all()
                admin_group.permissions = all_permissions
                
                db.session.commit()
                logger.info("Default admin group created successfully")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing group system: {e}")

# Decorator for checking group permissions
def group_permission_required(permission_name: str):
    """Decorator to require a specific group permission"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = user.get('id') or user.get('user_id')
            if not user_id:
                return jsonify({'error': 'User ID not found'}), 400
            
            # Check if user has the permission through any group
            user_groups = get_user_groups(user_id)
            has_permission = False
            
            for group in user_groups:
                if user_has_group_permission(user_id, group['id'], permission_name):
                    has_permission = True
                    break
            
            # Also check role-based permissions
            if not has_permission:
                user_role = get_user_role()
                if user_role:
                    try:
                        perm_enum = PermissionEnum(permission_name)
                        has_permission = PermissionManager.has_permission(user_role, perm_enum)
                    except ValueError:
                        pass
            
            if not has_permission:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
