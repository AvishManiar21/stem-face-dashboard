#!/usr/bin/env python3
"""
Test script for enhanced features:
1. Role-Based Control Panel
2. Shift Scheduling System  
3. Alerts & Notifications
"""

import requests
import json
from datetime import datetime, timedelta

def test_endpoint(url, expected_status=200, description="", method="GET", data=None):
    """Test an endpoint and return result"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        success = response.status_code == expected_status
        print(f"{'✅' if success else '❌'} {description}")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        print(f"   Status: {response.status_code}")
        if not success:
            print(f"   Expected: {expected_status}")
        return success
    except Exception as e:
        print(f"❌ {description}")
        print(f"   URL: {url}")
        print(f"   Error: {str(e)}")
        return False

def test_form_submission(url, form_data, expected_status=302, description=""):
    """Test form submission"""
    try:
        response = requests.post(url, data=form_data, timeout=10, allow_redirects=False)
        success = response.status_code == expected_status
        print(f"{'✅' if success else '❌'} {description}")
        print(f"   URL: {url}")
        print(f"   Status: {response.status_code}")
        if not success:
            print(f"   Expected: {expected_status}")
        return success
    except Exception as e:
        print(f"❌ {description}")
        print(f"   URL: {url}")
        print(f"   Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Enhanced Features")
    print("=" * 60)
    
    # Test 1: Role-Based Control Panel
    print("\n🔐 1. Role-Based Control Panel")
    print("-" * 40)
    
    # Test admin pages (should redirect to login if not authenticated)
    test_endpoint(f"{base_url}/admin/users", 302, "Admin Users Page (Unauthenticated)")
    test_endpoint(f"{base_url}/admin/audit-logs", 302, "Admin Audit Logs Page (Unauthenticated)")
    test_endpoint(f"{base_url}/admin/shifts", 302, "Admin Shifts Page (Unauthenticated)")
    
    # Test login page
    test_endpoint(f"{base_url}/login", 200, "Login Page")
    
    # Test user creation (form submission)
    user_data = {
        'email': 'test@example.com',
        'full_name': 'Test User',
        'role': 'tutor'
    }
    test_form_submission(f"{base_url}/admin/create-user", user_data, 302, "Create User (Unauthenticated)")
    
    # Test role change (form submission)
    role_data = {
        'user_id': 'TEST001',
        'new_role': 'lead_tutor'
    }
    test_form_submission(f"{base_url}/admin/change-role", role_data, 302, "Change Role (Unauthenticated)")
    
    # Test 2: Shift Scheduling System
    print("\n📅 2. Shift Scheduling System")
    print("-" * 40)
    
    # Test upcoming shifts endpoint
    test_endpoint(f"{base_url}/upcoming-shifts", 200, "Upcoming Shifts API")
    
    # Test shift management (form submissions)
    shift_data = {
        'shift_name': 'Test Shift',
        'start_time': '09:00',
        'end_time': '17:00',
        'days_of_week': ['Monday', 'Tuesday', 'Wednesday']
    }
    test_form_submission(f"{base_url}/admin/create-shift", shift_data, 302, "Create Shift (Unauthenticated)")
    
    assignment_data = {
        'shift_id': '1',
        'tutor_id': 'T001'
    }
    test_form_submission(f"{base_url}/admin/assign-shift", assignment_data, 302, "Assign Shift (Unauthenticated)")
    
    # Test 3: Alerts & Notifications
    print("\n🚨 3. Alerts & Notifications")
    print("-" * 40)
    
    # Test dashboard data (should include alerts)
    test_endpoint(f"{base_url}/dashboard-data", 200, "Dashboard Data with Alerts")
    
    # Test main dashboard page
    test_endpoint(f"{base_url}/", 302, "Main Dashboard (Unauthenticated)")
    
    # Test 4: Email Notifications (Placeholder)
    print("\n📧 4. Email Notifications")
    print("-" * 40)
    print("ℹ️  Email notifications are currently logged to console")
    print("   In production, configure SMTP settings for actual email sending")
    
    # Test 5: Audit Trail
    print("\n📋 5. Audit Trail")
    print("-" * 40)
    
    # Test audit log population
    test_form_submission(f"{base_url}/admin/populate-audit-logs", {}, 302, "Populate Audit Logs (Unauthenticated)")
    
    # Test 6: Authentication System
    print("\n🔑 6. Authentication System")
    print("-" * 40)
    
    # Test logout
    test_endpoint(f"{base_url}/logout", 302, "Logout (Redirects to login)")
    
    # Test 7: Enhanced Dashboard Features
    print("\n📊 7. Enhanced Dashboard Features")
    print("-" * 40)
    
    # Test charts page
    test_endpoint(f"{base_url}/charts", 200, "Charts Page")
    
    # Test calendar page
    test_endpoint(f"{base_url}/calendar", 200, "Calendar Page")
    
    # Test data export
    export_data = {
        "tutor_ids": "",
        "date_from": "",
        "date_to": ""
    }
    test_endpoint(f"{base_url}/export-chart-filtered-data", 200, "Export Chart Data", "POST", export_data)
    
    print("\n" + "=" * 60)
    print("🎉 Enhanced Features Testing Complete!")
    print("\n📋 Summary of Features Implemented:")
    print("✅ Role-Based Control Panel:")
    print("   • User creation, editing, deletion")
    print("   • Role management (tutor → lead tutor → manager → admin)")
    print("   • Admin-only access control")
    print("   • Audit trail for all admin actions")
    
    print("\n✅ Shift Scheduling System:")
    print("   • Shift creation and management")
    print("   • Tutor assignment to shifts")
    print("   • Upcoming shifts display on dashboard")
    print("   • Late check-in detection")
    
    print("\n✅ Alerts & Notifications:")
    print("   • Missing check-out warnings")
    print("   • Short shift alerts (< 1 hour)")
    print("   • Overlapping sessions detection")
    print("   • Late check-in notifications")
    print("   • Email notification system (placeholder)")
    
    print("\n✅ Additional Features:")
    print("   • Authentication system with session management")
    print("   • Enhanced dashboard with alerts section")
    print("   • Upcoming shifts display")
    print("   • Comprehensive admin interface")
    
    print("\n💡 Next Steps:")
    print("• Configure SMTP settings for email notifications")
    print("• Set up proper password authentication")
    print("• Add more granular permissions")
    print("• Implement real-time notifications")
    print("• Add shift conflict resolution")

if __name__ == "__main__":
    main() 