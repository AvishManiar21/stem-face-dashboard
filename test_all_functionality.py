#!/usr/bin/env python3
"""
Comprehensive test script to verify all functionality is working properly
"""

import requests
import json
from datetime import datetime

def test_endpoint(url, expected_status=200, description=""):
    """Test an endpoint and return result"""
    try:
        response = requests.get(url, timeout=10)
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

def test_post_endpoint(url, data, expected_status=200, description=""):
    """Test a POST endpoint and return result"""
    try:
        response = requests.post(url, json=data, timeout=10)
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
    
    print("🧪 Testing Tutor Dashboard Functionality")
    print("=" * 50)
    
    # Test main pages
    print("\n📄 Testing Main Pages:")
    test_endpoint(f"{base_url}/", description="Dashboard Page")
    test_endpoint(f"{base_url}/charts", description="Charts Page")
    test_endpoint(f"{base_url}/calendar", description="Calendar Page")
    
    # Test admin pages
    print("\n👨‍💼 Testing Admin Pages:")
    test_endpoint(f"{base_url}/admin/users", description="Admin Users Page")
    test_endpoint(f"{base_url}/admin/audit-logs", description="Admin Audit Logs Page")
    test_endpoint(f"{base_url}/admin/shifts", description="Admin Shifts Page")
    
    # Test API endpoints
    print("\n🔌 Testing API Endpoints:")
    test_endpoint(f"{base_url}/dashboard-data", description="Dashboard Data API")
    test_endpoint(f"{base_url}/get-tutors", description="Get Tutors API")
    test_endpoint(f"{base_url}/download-log", description="Download Log API")
    
    # Test chart data endpoint
    print("\n📊 Testing Chart Data:")
    chart_data = {
        "chartKey": "checkins_per_tutor",
        "tutor_ids": "",
        "date_from": "",
        "date_to": "",
        "chart_type": "bar"
    }
    test_post_endpoint(f"{base_url}/chart-data", chart_data, description="Chart Data API")
    
    # Test export functionality
    print("\n📤 Testing Export Functionality:")
    export_data = {
        "tutor_ids": "",
        "date_from": "",
        "date_to": ""
    }
    test_post_endpoint(f"{base_url}/export-chart-filtered-data", export_data, description="Export Chart Data")
    
    # Test admin functionality
    print("\n⚙️ Testing Admin Functionality:")
    
    # Test populate audit logs
    test_post_endpoint(f"{base_url}/admin/populate-audit-logs", {}, description="Populate Audit Logs")
    
    # Test create shift
    shift_data = {
        "shift_name": "Test Shift",
        "start_time": "09:00",
        "end_time": "17:00",
        "days_of_week": ["Monday", "Tuesday", "Wednesday"]
    }
    test_post_endpoint(f"{base_url}/admin/create-shift", shift_data, description="Create Shift")
    
    # Test assign shift
    assignment_data = {
        "shift_id": "1",
        "tutor_id": "T001"
    }
    test_post_endpoint(f"{base_url}/admin/assign-shift", assignment_data, description="Assign Shift")
    
    # Test remove assignment
    remove_data = {
        "assignment_id": "1"
    }
    test_post_endpoint(f"{base_url}/admin/remove-assignment", remove_data, description="Remove Assignment")
    
    # Test deactivate shift
    deactivate_data = {
        "shift_id": "1"
    }
    test_post_endpoint(f"{base_url}/admin/deactivate-shift", deactivate_data, description="Deactivate Shift")
    
    print("\n" + "=" * 50)
    print("🎉 Testing Complete!")
    print("\n📋 Summary:")
    print("• All main pages should be accessible")
    print("• All admin pages should be accessible")
    print("• All API endpoints should respond")
    print("• Chart functionality should work")
    print("• Export functionality should work")
    print("• Admin functionality should work")
    print("\n💡 If any tests failed, check:")
    print("• Application is running on http://localhost:5000")
    print("• All required files exist")
    print("• Database/CSV files are accessible")
    print("• No syntax errors in Python files")

if __name__ == "__main__":
    main() 