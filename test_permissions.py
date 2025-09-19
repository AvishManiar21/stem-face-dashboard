"""
Comprehensive Permission Testing Suite
Tests all permission-related functionality
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, g

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from permissions import (
    Permission, Role, ROLE_LEVELS, ROLE_PERMISSIONS, 
    PermissionManager, permission_required, permissions_required,
    role_required, can_modify_user, get_data_access_scope,
    filter_data_by_permissions, can_manage_users, can_view_analytics,
    can_export_data, can_manage_system
)
from permission_middleware import (
    PermissionContext, permission_context, require_data_access,
    api_permission_required, conditional_permission, data_filter_required,
    audit_permission_action, validate_user_modification, get_user_capabilities
)

class TestPermissionSystem(unittest.TestCase):
    """Test the core permission system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Flask(__name__)
        self.app.secret_key = 'test-secret-key'
        self.client = self.app.test_client()
    
    def test_role_hierarchy(self):
        """Test role hierarchy levels"""
        self.assertEqual(ROLE_LEVELS[Role.TUTOR], 1)
        self.assertEqual(ROLE_LEVELS[Role.LEAD_TUTOR], 2)
        self.assertEqual(ROLE_LEVELS[Role.MANAGER], 3)
        self.assertEqual(ROLE_LEVELS[Role.ADMIN], 4)
        self.assertEqual(ROLE_LEVELS[Role.SUPER_ADMIN], 5)
    
    def test_permission_assignments(self):
        """Test that roles have correct permissions"""
        # Tutor should have basic permissions
        tutor_perms = PermissionManager.get_user_permissions('tutor')
        self.assertIn(Permission.VIEW_OWN_DATA, tutor_perms)
        self.assertNotIn(Permission.CREATE_USERS, tutor_perms)
        
        # Admin should have most permissions
        admin_perms = PermissionManager.get_user_permissions('admin')
        self.assertIn(Permission.CREATE_USERS, admin_perms)
        self.assertIn(Permission.DELETE_USERS, admin_perms)
        self.assertIn(Permission.MANAGE_SYSTEM_SETTINGS, admin_perms)
        
        # Super admin should have all permissions
        super_admin_perms = PermissionManager.get_user_permissions('super_admin')
        self.assertEqual(len(super_admin_perms), len(Permission))
    
    def test_permission_checks(self):
        """Test permission checking functions"""
        # Test has_permission
        self.assertTrue(PermissionManager.has_permission('admin', Permission.CREATE_USERS))
        self.assertFalse(PermissionManager.has_permission('tutor', Permission.CREATE_USERS))
        
        # Test has_any_permission
        self.assertTrue(PermissionManager.has_any_permission('manager', [
            Permission.CREATE_USERS, Permission.VIEW_ANALYTICS
        ]))
        self.assertFalse(PermissionManager.has_any_permission('tutor', [
            Permission.CREATE_USERS, Permission.DELETE_USERS
        ]))
        
        # Test has_all_permissions
        self.assertTrue(PermissionManager.has_all_permissions('admin', [
            Permission.CREATE_USERS, Permission.EDIT_USERS
        ]))
        self.assertFalse(PermissionManager.has_all_permissions('tutor', [
            Permission.CREATE_USERS, Permission.EDIT_USERS
        ]))
    
    def test_role_access_control(self):
        """Test role-based access control"""
        # Admin can access manager role
        self.assertTrue(PermissionManager.can_access_role('manager', 'admin'))
        
        # Manager cannot access admin role
        self.assertFalse(PermissionManager.can_access_role('admin', 'manager'))
        
        # Same role cannot access itself
        self.assertFalse(PermissionManager.can_access_role('admin', 'admin'))
    
    def test_data_access_scope(self):
        """Test data access scope determination"""
        self.assertEqual(get_data_access_scope('admin'), 'all')
        self.assertEqual(get_data_access_scope('manager'), 'all')
        self.assertEqual(get_data_access_scope('lead_tutor'), 'team')
        self.assertEqual(get_data_access_scope('tutor'), 'own')
        self.assertEqual(get_data_access_scope('unknown'), 'none')
    
    def test_convenience_functions(self):
        """Test convenience permission functions"""
        # Test can_manage_users
        self.assertTrue(can_manage_users('admin'))
        self.assertTrue(can_manage_users('manager'))
        self.assertFalse(can_manage_users('tutor'))
        
        # Test can_view_analytics
        self.assertTrue(can_view_analytics('admin'))
        self.assertTrue(can_view_analytics('lead_tutor'))
        self.assertFalse(can_view_analytics('tutor'))
        
        # Test can_export_data
        self.assertTrue(can_export_data('admin'))
        self.assertTrue(can_export_data('manager'))
        self.assertFalse(can_export_data('tutor'))
        
        # Test can_manage_system
        self.assertTrue(can_manage_system('admin'))
        self.assertFalse(can_manage_system('manager'))
        self.assertFalse(can_manage_system('tutor'))

class TestPermissionMiddleware(unittest.TestCase):
    """Test permission middleware functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Flask(__name__)
        self.app.secret_key = 'test-secret-key'
        self.client = self.app.test_client()
    
    def test_permission_context(self):
        """Test permission context creation"""
        context = PermissionContext()
        
        # Mock user data
        context.user = {
            'email': 'test@example.com',
            'user_metadata': {'role': 'admin', 'tutor_id': '123'}
        }
        context.role = 'admin'
        context.tutor_id = '123'
        context.load_user_context()
        
        self.assertEqual(context.role, 'admin')
        self.assertEqual(context.tutor_id, '123')
        self.assertIn(Permission.CREATE_USERS, context.permissions)
    
    @patch('permission_middleware.get_current_user')
    @patch('permission_middleware.get_user_role')
    @patch('permission_middleware.get_user_tutor_id')
    def test_permission_decorators(self, mock_tutor_id, mock_role, mock_user):
        """Test permission decorators"""
        # Mock user data
        mock_user.return_value = {'email': 'test@example.com'}
        mock_role.return_value = 'admin'
        mock_tutor_id.return_value = '123'
        
        @self.app.route('/test-permission')
        @permission_context
        @api_permission_required(Permission.CREATE_USERS)
        def test_route():
            return {'success': True}
        
        with self.app.test_client() as client:
            response = client.get('/test-permission')
            # Should succeed for admin user
            self.assertEqual(response.status_code, 200)
    
    def test_data_filtering(self):
        """Test data filtering based on permissions"""
        import pandas as pd
        
        # Create test data
        data = {
            'tutor_id': ['1', '2', '3'],
            'tutor_name': ['John', 'Jane', 'Bob'],
            'score': [85, 90, 78]
        }
        df = pd.DataFrame(data)
        
        # Test admin access (should see all data)
        filtered_admin = filter_data_by_permissions(df, 'admin', '1', 'admin@test.com')
        self.assertEqual(len(filtered_admin), 3)
        
        # Test tutor access (should see only own data)
        filtered_tutor = filter_data_by_permissions(df, 'tutor', '1', 'tutor@test.com')
        self.assertEqual(len(filtered_tutor), 1)
        self.assertEqual(filtered_tutor.iloc[0]['tutor_id'], '1')

class TestPermissionIntegration(unittest.TestCase):
    """Test integration between permission system and Flask app"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Flask(__name__)
        self.app.secret_key = 'test-secret-key'
        self.client = self.app.test_client()
    
    @patch('permission_middleware.get_current_user')
    @patch('permission_middleware.get_user_role')
    def test_api_endpoints(self, mock_role, mock_user):
        """Test API endpoints with permission system"""
        # Mock admin user
        mock_user.return_value = {
            'email': 'admin@test.com',
            'user_metadata': {'role': 'admin'}
        }
        mock_role.return_value = 'admin'
        
        @self.app.route('/api/test')
        @permission_context
        @api_permission_required(Permission.VIEW_USERS)
        def test_endpoint():
            return {'message': 'success'}
        
        with self.app.test_client() as client:
            response = client.get('/api/test')
            self.assertEqual(response.status_code, 200)
    
    def test_error_responses(self):
        """Test error responses for permission failures"""
        @self.app.route('/api/unauthorized')
        @permission_context
        @api_permission_required(Permission.CREATE_USERS)
        def unauthorized_endpoint():
            return {'message': 'success'}
        
        with self.app.test_client() as client:
            # No user logged in
            response = client.get('/api/unauthorized')
            self.assertEqual(response.status_code, 401)
            
            data = response.get_json()
            self.assertEqual(data['error']['code'], 'AUTH_REQUIRED')

class TestPermissionSecurity(unittest.TestCase):
    """Test security aspects of permission system"""
    
    def test_permission_escalation_prevention(self):
        """Test that users cannot escalate their own permissions"""
        # Regular user should not be able to access admin functions
        self.assertFalse(PermissionManager.has_permission('tutor', Permission.CREATE_USERS))
        self.assertFalse(PermissionManager.has_permission('tutor', Permission.DELETE_USERS))
        
        # Manager should not be able to access super admin functions
        self.assertFalse(PermissionManager.has_permission('manager', Permission.MANAGE_SYSTEM_SETTINGS))
    
    def test_role_modification_restrictions(self):
        """Test restrictions on role modifications"""
        # Manager cannot promote to admin
        self.assertFalse(PermissionManager.can_access_role('admin', 'manager'))
        
        # Admin can modify manager
        self.assertTrue(PermissionManager.can_access_role('manager', 'admin'))
        
        # Same role cannot modify itself
        self.assertFalse(PermissionManager.can_access_role('admin', 'admin'))
    
    def test_data_access_isolation(self):
        """Test that data access is properly isolated"""
        import pandas as pd
        
        # Create test data with multiple users
        data = {
            'tutor_id': ['1', '2', '3'],
            'tutor_name': ['User1', 'User2', 'User3'],
            'sensitive_data': ['secret1', 'secret2', 'secret3']
        }
        df = pd.DataFrame(data)
        
        # User 1 should only see their own data
        filtered = filter_data_by_permissions(df, 'tutor', '1', 'user1@test.com')
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered.iloc[0]['tutor_id'], '1')
        
        # Admin should see all data
        filtered_admin = filter_data_by_permissions(df, 'admin', '1', 'admin@test.com')
        self.assertEqual(len(filtered_admin), 3)

def run_permission_tests():
    """Run all permission tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPermissionSystem,
        TestPermissionMiddleware,
        TestPermissionIntegration,
        TestPermissionSecurity
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_permission_tests()
    sys.exit(0 if success else 1)
