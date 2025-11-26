"""Test script to verify admin settings routes work"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app.admin.routes import admin_bp
from app.utils.feature_flags import get_all_features, toggle_feature, is_feature_enabled

def test_settings_routes():
    """Test the admin settings routes"""
    print("=" * 60)
    print("Testing Admin Settings Routes")
    print("=" * 60)
    
    # Create a test Flask app
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    with app.test_client() as client:
        # Test GET /admin/settings
        print("\n1. Testing GET /admin/settings...")
        response = client.get('/admin/settings')
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   [OK] Settings page loads successfully")
            # Check if features are in the response
            if b'feature-toggle' in response.data or b'face_recognition' in response.data:
                print("   [OK] Features are rendered in the page")
            else:
                print("   [WARNING] Features may not be rendered")
        else:
            print(f"   [ERROR] Failed to load settings page")
        
        # Test POST /admin/settings/save
        print("\n2. Testing POST /admin/settings/save...")
        
        # Get initial state
        initial_state = is_feature_enabled('face_recognition')
        print(f"   Initial state of face_recognition: {initial_state}")
        
        # Test toggling ON
        test_data = {'face_recognition': True}
        response = client.post('/admin/settings/save', 
                              json=test_data,
                              content_type='application/json')
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"   Response: {data}")
            if data.get('success'):
                print("   [OK] Feature toggle saved successfully")
                # Verify it was actually saved
                new_state = is_feature_enabled('face_recognition')
                if new_state == True:
                    print("   [OK] Feature state verified in database")
                else:
                    print(f"   [ERROR] Feature state mismatch: expected True, got {new_state}")
            else:
                print(f"   [ERROR] Save failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"   [ERROR] Request failed with status {response.status_code}")
            print(f"   Response: {response.get_data(as_text=True)}")
        
        # Restore initial state
        print(f"\n3. Restoring initial state...")
        toggle_feature('face_recognition', initial_state)
        print("   [OK] Initial state restored")
    
    print("\n" + "=" * 60)
    print("Route Test Complete!")
    print("=" * 60)

if __name__ == '__main__':
    test_settings_routes()

