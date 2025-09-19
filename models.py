"""
SQLAlchemy models for user grouping and permission control
Compatible with Flask-Login and Flask-SQLAlchemy
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Initialize SQLAlchemy
db = SQLAlchemy()

# Association table for many-to-many relationship between groups and permissions
group_permissions = Table(
    'group_permissions',
    db.Model.metadata,
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class Group(db.Model):
    """Group model for organizing users"""
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    lead_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)
    
    # Relationships
    lead_user = relationship("User", foreign_keys=[lead_user_id], back_populates="led_groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    permissions = relationship("Permission", secondary=group_permissions, back_populates="groups")
    
    def __repr__(self):
        return f'<Group {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'lead_user_id': self.lead_user_id,
            'lead_user_name': self.lead_user.full_name if self.lead_user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'active': self.active,
            'member_count': len(self.members)
        }

class GroupMember(db.Model):
    """Group membership model"""
    __tablename__ = 'group_members'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String(50), default='member')  # member, moderator, etc.
    active = Column(Boolean, default=True)
    
    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")
    
    # Unique constraint to prevent duplicate memberships
    __table_args__ = (db.UniqueConstraint('group_id', 'user_id', name='unique_group_membership'),)
    
    def __repr__(self):
        return f'<GroupMember {self.user.email} in {self.group.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'role': self.role,
            'active': self.active
        }

class Permission(db.Model):
    """Permission model for granular access control"""
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(50))  # user_management, data_access, analytics, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    
    # Relationships
    groups = relationship("Group", secondary=group_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'active': self.active
        }

class GroupPermission(db.Model):
    """Explicit group-permission assignments (if needed for additional metadata)"""
    __tablename__ = 'group_permission_assignments'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permissions.id'), nullable=False)
    granted_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    active = Column(Boolean, default=True)
    
    # Relationships
    group = relationship("Group")
    permission = relationship("Permission")
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    
    def __repr__(self):
        return f'<GroupPermission {self.group.name} -> {self.permission.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'permission_id': self.permission_id,
            'permission_name': self.permission.name if self.permission else None,
            'granted_by': self.granted_by,
            'granted_by_name': self.granted_by_user.full_name if self.granted_by_user else None,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'active': self.active
        }

# User model extension (assuming you have a User model)
# This would be added to your existing User model
class User(db.Model):
    """Extended User model with group relationships"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    full_name = Column(String(100))
    role = Column(String(50), default='tutor')
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Group relationships
    led_groups = relationship("Group", foreign_keys="Group.lead_user_id", back_populates="lead_user")
    group_memberships = relationship("GroupMember", back_populates="user")
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def get_groups(self):
        """Get all groups this user belongs to"""
        return [membership.group for membership in self.group_memberships if membership.active]
    
    def get_led_groups(self):
        """Get all groups this user leads"""
        return [group for group in self.led_groups if group.active]
    
    def is_group_lead(self, group_id):
        """Check if user is the lead of a specific group"""
        return any(group.id == group_id for group in self.get_led_groups())
    
    def is_group_member(self, group_id):
        """Check if user is a member of a specific group"""
        return any(membership.group_id == group_id and membership.active 
                  for membership in self.group_memberships)
