"""
Database initialization script for user grouping and permission system
Run this script to set up the database tables and initial data
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import models
from models import db, Group, GroupMember, Permission, GroupPermission, User

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    
    # Database configuration
    # You can modify this to use your existing database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///group_system.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    return app

def create_tables(app):
    """Create all database tables"""
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created successfully")
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            return False
    return True

def create_default_permissions():
    """Create default permissions"""
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
                'name': 'change_user_roles',
                'description': 'Change user roles',
                'category': 'user_management'
            },
            {
                'name': 'activate_deactivate_users',
                'description': 'Activate or deactivate users',
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
        
        created_count = 0
        for perm_data in default_permissions:
            existing = Permission.query.filter_by(name=perm_data['name']).first()
            if not existing:
                permission = Permission(
                    name=perm_data['name'],
                    description=perm_data['description'],
                    category=perm_data['category']
                )
                db.session.add(permission)
                created_count += 1
        
        db.session.commit()
        print(f"✓ Created {created_count} default permissions")
        return True
        
    except Exception as e:
        print(f"✗ Error creating default permissions: {e}")
        db.session.rollback()
        return False

def create_sample_users():
    """Create sample users for testing"""
    try:
        sample_users = [
            {
                'email': 'admin@example.com',
                'full_name': 'System Administrator',
                'role': 'admin'
            },
            {
                'email': 'manager@example.com',
                'full_name': 'Manager User',
                'role': 'manager'
            },
            {
                'email': 'lead@example.com',
                'full_name': 'Lead Tutor',
                'role': 'lead_tutor'
            },
            {
                'email': 'tutor1@example.com',
                'full_name': 'Tutor One',
                'role': 'tutor'
            },
            {
                'email': 'tutor2@example.com',
                'full_name': 'Tutor Two',
                'role': 'tutor'
            }
        ]
        
        created_count = 0
        for user_data in sample_users:
            existing = User.query.filter_by(email=user_data['email']).first()
            if not existing:
                user = User(
                    email=user_data['email'],
                    full_name=user_data['full_name'],
                    role=user_data['role'],
                    active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(user)
                created_count += 1
        
        db.session.commit()
        print(f"✓ Created {created_count} sample users")
        return True
        
    except Exception as e:
        print(f"✗ Error creating sample users: {e}")
        db.session.rollback()
        return False

def create_sample_groups():
    """Create sample groups for testing"""
    try:
        # Get admin user to be group lead
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            print("✗ No admin user found. Please create users first.")
            return False
        
        # Get manager user
        manager_user = User.query.filter_by(role='manager').first()
        if not manager_user:
            print("✗ No manager user found. Please create users first.")
            return False
        
        sample_groups = [
            {
                'name': 'Administrators',
                'description': 'System administrators group',
                'lead_user_id': admin_user.id
            },
            {
                'name': 'Managers',
                'description': 'Management team group',
                'lead_user_id': manager_user.id
            },
            {
                'name': 'Tutor Team A',
                'description': 'Tutor team for morning shifts',
                'lead_user_id': admin_user.id
            },
            {
                'name': 'Tutor Team B',
                'description': 'Tutor team for evening shifts',
                'lead_user_id': manager_user.id
            }
        ]
        
        created_count = 0
        for group_data in sample_groups:
            existing = Group.query.filter_by(name=group_data['name']).first()
            if not existing:
                group = Group(
                    name=group_data['name'],
                    description=group_data['description'],
                    lead_user_id=group_data['lead_user_id']
                )
                db.session.add(group)
                db.session.flush()  # Get the group ID
                
                # Add lead user as a member
                group_member = GroupMember(
                    group_id=group.id,
                    user_id=group_data['lead_user_id'],
                    role='lead'
                )
                db.session.add(group_member)
                created_count += 1
        
        db.session.commit()
        print(f"✓ Created {created_count} sample groups")
        return True
        
    except Exception as e:
        print(f"✗ Error creating sample groups: {e}")
        db.session.rollback()
        return False

def assign_permissions_to_groups():
    """Assign permissions to groups"""
    try:
        # Get all groups
        groups = Group.query.all()
        # Get all permissions
        permissions = Permission.query.all()
        
        if not groups or not permissions:
            print("✗ No groups or permissions found")
            return False
        
        # Assign permissions based on group type
        for group in groups:
            if 'Administrator' in group.name:
                # Administrators get all permissions
                group.permissions = permissions
            elif 'Manager' in group.name:
                # Managers get most permissions except system settings
                manager_permissions = [p for p in permissions if p.name != 'manage_system_settings']
                group.permissions = manager_permissions
            elif 'Tutor Team' in group.name:
                # Tutor teams get basic permissions
                tutor_permissions = [p for p in permissions if p.category in ['data_access', 'analytics']]
                group.permissions = tutor_permissions
        
        db.session.commit()
        print("✓ Assigned permissions to groups")
        return True
        
    except Exception as e:
        print(f"✗ Error assigning permissions to groups: {e}")
        db.session.rollback()
        return False

def add_users_to_groups():
    """Add users to appropriate groups"""
    try:
        # Get users and groups
        users = User.query.all()
        admin_group = Group.query.filter_by(name='Administrators').first()
        manager_group = Group.query.filter_by(name='Managers').first()
        tutor_groups = Group.query.filter(Group.name.like('%Tutor Team%')).all()
        
        if not users or not admin_group:
            print("✗ No users or admin group found")
            return False
        
        added_count = 0
        for user in users:
            if user.role == 'admin' and admin_group:
                # Add admin to admin group if not already a member
                existing = GroupMember.query.filter_by(
                    group_id=admin_group.id,
                    user_id=user.id
                ).first()
                if not existing:
                    member = GroupMember(
                        group_id=admin_group.id,
                        user_id=user.id,
                        role='member'
                    )
                    db.session.add(member)
                    added_count += 1
            
            elif user.role == 'manager' and manager_group:
                # Add manager to manager group if not already a member
                existing = GroupMember.query.filter_by(
                    group_id=manager_group.id,
                    user_id=user.id
                ).first()
                if not existing:
                    member = GroupMember(
                        group_id=manager_group.id,
                        user_id=user.id,
                        role='member'
                    )
                    db.session.add(member)
                    added_count += 1
            
            elif user.role == 'tutor' and tutor_groups:
                # Add tutors to tutor groups (distribute evenly)
                for i, group in enumerate(tutor_groups):
                    if i % 2 == 0:  # Add to first group
                        existing = GroupMember.query.filter_by(
                            group_id=group.id,
                            user_id=user.id
                        ).first()
                        if not existing:
                            member = GroupMember(
                                group_id=group.id,
                                user_id=user.id,
                                role='member'
                            )
                            db.session.add(member)
                            added_count += 1
                            break
        
        db.session.commit()
        print(f"✓ Added {added_count} users to groups")
        return True
        
    except Exception as e:
        print(f"✗ Error adding users to groups: {e}")
        db.session.rollback()
        return False

def main():
    """Main initialization function"""
    print("Initializing User Grouping and Permission System...")
    print("=" * 50)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        # Create tables
        if not create_tables(app):
            print("Failed to create tables. Exiting.")
            return False
        
        # Create default permissions
        if not create_default_permissions():
            print("Failed to create default permissions. Exiting.")
            return False
        
        # Create sample users
        if not create_sample_users():
            print("Failed to create sample users. Exiting.")
            return False
        
        # Create sample groups
        if not create_sample_groups():
            print("Failed to create sample groups. Exiting.")
            return False
        
        # Assign permissions to groups
        if not assign_permissions_to_groups():
            print("Failed to assign permissions to groups. Exiting.")
            return False
        
        # Add users to groups
        if not add_users_to_groups():
            print("Failed to add users to groups. Exiting.")
            return False
    
    print("=" * 50)
    print("✓ User Grouping and Permission System initialized successfully!")
    print("\nNext steps:")
    print("1. Update your main app.py to include the group routes")
    print("2. Add the group management template to your templates")
    print("3. Test the system with the sample users")
    print("\nSample users created:")
    print("- admin@example.com (admin)")
    print("- manager@example.com (manager)")
    print("- lead@example.com (lead_tutor)")
    print("- tutor1@example.com (tutor)")
    print("- tutor2@example.com (tutor)")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
