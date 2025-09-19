"""
Test script for the user grouping and permission system
Run this to verify the system is working correctly
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Group, GroupMember, Permission, GroupPermission, User
from group_helpers import (
    user_has_group_permission, 
    get_user_all_permissions, 
    get_user_groups,
    can_user_access_group,
    can_user_manage_group
)

def create_test_app():
    """Create test Flask app"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_group_system.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    
    db.init_app(app)
    return app

def test_database_creation():
    """Test database table creation"""
    print("Testing database creation...")
    
    app = create_test_app()
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created successfully")
            return True
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            return False

def test_permission_creation():
    """Test permission creation"""
    print("Testing permission creation...")
    
    app = create_test_app()
    with app.app_context():
        try:
            db.create_all()
            
            # Create a test permission
            permission = Permission(
                name='test_permission',
                description='Test permission for testing',
                category='test'
            )
            db.session.add(permission)
            db.session.commit()
            
            # Verify it was created
            created_permission = Permission.query.filter_by(name='test_permission').first()
            if created_permission:
                print("✓ Permission created successfully")
                return True
            else:
                print("✗ Permission not found after creation")
                return False
                
        except Exception as e:
            print(f"✗ Error creating permission: {e}")
            db.session.rollback()
            return False

def test_user_creation():
    """Test user creation"""
    print("Testing user creation...")
    
    app = create_test_app()
    with app.app_context():
        try:
            db.create_all()
            
            # Create a test user
            user = User(
                email='test@example.com',
                full_name='Test User',
                role='tutor',
                active=True
            )
            db.session.add(user)
            db.session.commit()
            
            # Verify it was created
            created_user = User.query.filter_by(email='test@example.com').first()
            if created_user:
                print("✓ User created successfully")
                return True
            else:
                print("✗ User not found after creation")
                return False
                
        except Exception as e:
            print(f"✗ Error creating user: {e}")
            db.session.rollback()
            return False

def test_group_creation():
    """Test group creation"""
    print("Testing group creation...")
    
    app = create_test_app()
    with app.app_context():
        try:
            db.create_all()
            
            # Create a test user first
            user = User(
                email='test@example.com',
                full_name='Test User',
                role='tutor',
                active=True
            )
            db.session.add(user)
            db.session.commit()
            
            # Create a test group
            group = Group(
                name='Test Group',
                description='Test group for testing',
                lead_user_id=user.id
            )
            db.session.add(group)
            db.session.flush()  # Get the group ID
            
            # Add user as member
            group_member = GroupMember(
                group_id=group.id,
                user_id=user.id,
                role='lead'
            )
            db.session.add(group_member)
            db.session.commit()
            
            # Verify it was created
            created_group = Group.query.filter_by(name='Test Group').first()
            if created_group:
                print("✓ Group created successfully")
                return True
            else:
                print("✗ Group not found after creation")
                return False
                
        except Exception as e:
            print(f"✗ Error creating group: {e}")
            db.session.rollback()
            return False

def test_permission_helpers():
    """Test permission helper functions"""
    print("Testing permission helper functions...")
    
    app = create_test_app()
    with app.app_context():
        try:
            db.create_all()
            
            # Create test data
            user = User(
                email='test@example.com',
                full_name='Test User',
                role='tutor',
                active=True
            )
            db.session.add(user)
            db.session.commit()
            
            permission = Permission(
                name='test_permission',
                description='Test permission',
                category='test'
            )
            db.session.add(permission)
            db.session.commit()
            
            group = Group(
                name='Test Group',
                description='Test group',
                lead_user_id=user.id
            )
            db.session.add(group)
            db.session.flush()
            
            # Add permission to group
            group.permissions.append(permission)
            
            # Add user to group
            group_member = GroupMember(
                group_id=group.id,
                user_id=user.id,
                role='member'
            )
            db.session.add(group_member)
            db.session.commit()
            
            # Test helper functions
            user_id = user.id
            group_id = group.id
            
            # Test user_has_group_permission
            has_permission = user_has_group_permission(user_id, group_id, 'test_permission')
            if has_permission:
                print("✓ user_has_group_permission works")
            else:
                print("✗ user_has_group_permission failed")
                return False
            
            # Test get_user_groups
            user_groups = get_user_groups(user_id)
            if user_groups and len(user_groups) > 0:
                print("✓ get_user_groups works")
            else:
                print("✗ get_user_groups failed")
                return False
            
            # Test get_user_all_permissions
            all_permissions = get_user_all_permissions(user_id)
            if 'test_permission' in all_permissions:
                print("✓ get_user_all_permissions works")
            else:
                print("✗ get_user_all_permissions failed")
                return False
            
            # Test can_user_access_group
            can_access = can_user_access_group(user_id, group_id)
            if can_access:
                print("✓ can_user_access_group works")
            else:
                print("✗ can_user_access_group failed")
                return False
            
            # Test can_user_manage_group
            can_manage = can_user_manage_group(user_id, group_id)
            if can_manage:
                print("✓ can_user_manage_group works")
            else:
                print("✗ can_user_manage_group failed")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Error testing helper functions: {e}")
            db.session.rollback()
            return False

def test_api_endpoints():
    """Test API endpoints (basic functionality)"""
    print("Testing API endpoints...")
    
    app = create_test_app()
    with app.app_context():
        try:
            db.create_all()
            
            # Import and register the blueprint
            from group_routes import group_bp
            app.register_blueprint(group_bp)
            
            # Create test client
            client = app.test_client()
            
            # Test permissions endpoint
            response = client.get('/groups/permissions')
            if response.status_code == 200:
                print("✓ Permissions endpoint works")
            else:
                print(f"✗ Permissions endpoint failed: {response.status_code}")
                return False
            
            # Test users endpoint
            response = client.get('/groups/users')
            if response.status_code == 200:
                print("✓ Users endpoint works")
            else:
                print(f"✗ Users endpoint failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Error testing API endpoints: {e}")
            return False

def main():
    """Run all tests"""
    print("Running User Grouping and Permission System Tests")
    print("=" * 50)
    
    tests = [
        test_database_creation,
        test_permission_creation,
        test_user_creation,
        test_group_creation,
        test_permission_helpers,
        test_api_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed! The group system is working correctly.")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
