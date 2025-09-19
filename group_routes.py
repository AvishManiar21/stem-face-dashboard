"""
Flask routes for user grouping and permission management
"""

from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from functools import wraps
from datetime import datetime
import logging
from models import db, Group, GroupMember, Permission, GroupPermission, User
from auth import get_current_user, get_user_role
from permissions import Permission as PermissionEnum, PermissionManager, permission_required

logger = logging.getLogger(__name__)

# Create blueprint
group_bp = Blueprint('groups', __name__, url_prefix='/groups')

def group_lead_required(f):
    """Decorator to require group lead permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user is admin/manager (can manage all groups)
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            return f(*args, **kwargs)
        
        # Check if user is group lead for the specific group
        group_id = request.view_args.get('group_id')
        if group_id:
            user_id = user.get('id') or user.get('user_id')
            if user_id:
                user_obj = User.query.get(user_id)
                if user_obj and user_obj.is_group_lead(group_id):
                    return f(*args, **kwargs)
        
        return jsonify({'error': 'Insufficient permissions'}), 403
    return decorated_function

@group_bp.route('/')
@permission_required(PermissionEnum.VIEW_USERS)
def list_groups():
    """List all groups"""
    try:
        groups = Group.query.filter_by(active=True).all()
        return jsonify([group.to_dict() for group in groups])
    except Exception as e:
        logger.error(f"Error listing groups: {e}")
        return jsonify({'error': 'Failed to list groups'}), 500

@group_bp.route('/create', methods=['POST'])
@permission_required(PermissionEnum.CREATE_USERS)
def create_group():
    """Create a new group with a lead user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Group name is required'}), 400
        
        if not data.get('lead_user_id'):
            return jsonify({'error': 'Lead user ID is required'}), 400
        
        # Check if group name already exists
        existing_group = Group.query.filter_by(name=data['name']).first()
        if existing_group:
            return jsonify({'error': 'Group name already exists'}), 400
        
        # Verify lead user exists
        lead_user = User.query.get(data['lead_user_id'])
        if not lead_user:
            return jsonify({'error': 'Lead user not found'}), 404
        
        # Create group
        group = Group(
            name=data['name'],
            description=data.get('description', ''),
            lead_user_id=data['lead_user_id']
        )
        
        db.session.add(group)
        db.session.flush()  # Get the group ID
        
        # Add lead user as a member
        group_member = GroupMember(
            group_id=group.id,
            user_id=data['lead_user_id'],
            role='lead'
        )
        db.session.add(group_member)
        
        db.session.commit()
        
        logger.info(f"Group '{group.name}' created with lead user {lead_user.email}")
        return jsonify({
            'message': 'Group created successfully',
            'group': group.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating group: {e}")
        return jsonify({'error': 'Failed to create group'}), 500

@group_bp.route('/<int:group_id>')
@permission_required(PermissionEnum.VIEW_USERS)
def get_group(group_id):
    """Get group details"""
    try:
        group = Group.query.get_or_404(group_id)
        return jsonify(group.to_dict())
    except Exception as e:
        logger.error(f"Error getting group {group_id}: {e}")
        return jsonify({'error': 'Failed to get group'}), 500

@group_bp.route('/<int:group_id>/members')
@permission_required(PermissionEnum.VIEW_USERS)
def get_group_members(group_id):
    """Get group members"""
    try:
        group = Group.query.get_or_404(group_id)
        members = GroupMember.query.filter_by(group_id=group_id, active=True).all()
        return jsonify([member.to_dict() for member in members])
    except Exception as e:
        logger.error(f"Error getting group members for {group_id}: {e}")
        return jsonify({'error': 'Failed to get group members'}), 500

@group_bp.route('/<int:group_id>/add-member', methods=['POST'])
@group_lead_required
def add_group_member(group_id):
    """Add a user to a group"""
    try:
        data = request.get_json()
        
        if not data.get('user_id'):
            return jsonify({'error': 'User ID is required'}), 400
        
        # Verify group exists
        group = Group.query.get_or_404(group_id)
        
        # Verify user exists
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user is already a member
        existing_member = GroupMember.query.filter_by(
            group_id=group_id, 
            user_id=data['user_id']
        ).first()
        
        if existing_member:
            if existing_member.active:
                return jsonify({'error': 'User is already a member of this group'}), 400
            else:
                # Reactivate membership
                existing_member.active = True
                existing_member.joined_at = datetime.utcnow()
                existing_member.role = data.get('role', 'member')
        else:
            # Create new membership
            group_member = GroupMember(
                group_id=group_id,
                user_id=data['user_id'],
                role=data.get('role', 'member')
            )
            db.session.add(group_member)
        
        db.session.commit()
        
        logger.info(f"User {user.email} added to group {group.name}")
        return jsonify({'message': 'User added to group successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding member to group {group_id}: {e}")
        return jsonify({'error': 'Failed to add member to group'}), 500

@group_bp.route('/<int:group_id>/remove-member', methods=['POST'])
@group_lead_required
def remove_group_member(group_id):
    """Remove a user from a group"""
    try:
        data = request.get_json()
        
        if not data.get('user_id'):
            return jsonify({'error': 'User ID is required'}), 400
        
        # Find membership
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=data['user_id']
        ).first()
        
        if not membership:
            return jsonify({'error': 'User is not a member of this group'}), 404
        
        # Don't allow removing the group lead
        if membership.role == 'lead':
            return jsonify({'error': 'Cannot remove group lead'}), 400
        
        # Deactivate membership instead of deleting
        membership.active = False
        db.session.commit()
        
        logger.info(f"User {membership.user.email} removed from group {group_id}")
        return jsonify({'message': 'User removed from group successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing member from group {group_id}: {e}")
        return jsonify({'error': 'Failed to remove member from group'}), 500

@group_bp.route('/<int:group_id>/permissions')
@permission_required(PermissionEnum.VIEW_USERS)
def get_group_permissions(group_id):
    """Get group permissions"""
    try:
        group = Group.query.get_or_404(group_id)
        permissions = group.permissions
        return jsonify([permission.to_dict() for permission in permissions])
    except Exception as e:
        logger.error(f"Error getting group permissions for {group_id}: {e}")
        return jsonify({'error': 'Failed to get group permissions'}), 500

@group_bp.route('/<int:group_id>/assign-permission', methods=['POST'])
@group_lead_required
def assign_group_permission(group_id):
    """Assign a permission to a group"""
    try:
        data = request.get_json()
        
        if not data.get('permission_id'):
            return jsonify({'error': 'Permission ID is required'}), 400
        
        # Verify group exists
        group = Group.query.get_or_404(group_id)
        
        # Verify permission exists
        permission = Permission.query.get(data['permission_id'])
        if not permission:
            return jsonify({'error': 'Permission not found'}), 404
        
        # Check if permission is already assigned
        if permission in group.permissions:
            return jsonify({'error': 'Permission is already assigned to this group'}), 400
        
        # Add permission to group
        group.permissions.append(permission)
        
        # Create explicit assignment record
        current_user = get_current_user()
        assignment = GroupPermission(
            group_id=group_id,
            permission_id=data['permission_id'],
            granted_by=current_user.get('id') or current_user.get('user_id')
        )
        db.session.add(assignment)
        
        db.session.commit()
        
        logger.info(f"Permission {permission.name} assigned to group {group.name}")
        return jsonify({'message': 'Permission assigned successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error assigning permission to group {group_id}: {e}")
        return jsonify({'error': 'Failed to assign permission'}), 500

@group_bp.route('/<int:group_id>/remove-permission', methods=['POST'])
@group_lead_required
def remove_group_permission(group_id):
    """Remove a permission from a group"""
    try:
        data = request.get_json()
        
        if not data.get('permission_id'):
            return jsonify({'error': 'Permission ID is required'}), 400
        
        # Verify group exists
        group = Group.query.get_or_404(group_id)
        
        # Verify permission exists
        permission = Permission.query.get(data['permission_id'])
        if not permission:
            return jsonify({'error': 'Permission not found'}), 404
        
        # Check if permission is assigned
        if permission not in group.permissions:
            return jsonify({'error': 'Permission is not assigned to this group'}), 400
        
        # Remove permission from group
        group.permissions.remove(permission)
        
        # Deactivate assignment record
        assignment = GroupPermission.query.filter_by(
            group_id=group_id,
            permission_id=data['permission_id']
        ).first()
        if assignment:
            assignment.active = False
        
        db.session.commit()
        
        logger.info(f"Permission {permission.name} removed from group {group.name}")
        return jsonify({'message': 'Permission removed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing permission from group {group_id}: {e}")
        return jsonify({'error': 'Failed to remove permission'}), 500

@group_bp.route('/permissions')
@permission_required(PermissionEnum.VIEW_USERS)
def list_permissions():
    """List all available permissions"""
    try:
        permissions = Permission.query.filter_by(active=True).all()
        return jsonify([permission.to_dict() for permission in permissions])
    except Exception as e:
        logger.error(f"Error listing permissions: {e}")
        return jsonify({'error': 'Failed to list permissions'}), 500

@group_bp.route('/users')
@permission_required(PermissionEnum.VIEW_USERS)
def list_users():
    """List all users for group management"""
    try:
        users = User.query.filter_by(active=True).all()
        return jsonify([user.to_dict() for user in users])
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({'error': 'Failed to list users'}), 500

# Helper function to check if user has permission in group
def user_has_group_permission(user_id, group_id, permission_name):
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

# Helper function to get user's groups
def get_user_groups(user_id):
    """Get all groups a user belongs to"""
    try:
        user = User.query.get(user_id)
        if not user:
            return []
        
        return [group.to_dict() for group in user.get_groups()]
    except Exception as e:
        logger.error(f"Error getting user groups: {e}")
        return []

# Helper function to get user's permissions across all groups
def get_user_group_permissions(user_id):
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
