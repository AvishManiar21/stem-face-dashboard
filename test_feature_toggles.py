"""Test script to verify feature flag toggling system works"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.feature_flags import (
    is_feature_enabled,
    toggle_feature,
    get_all_features,
    ensure_config_file
)
import pandas as pd

def test_feature_toggles():
    """Test the feature flag system"""
    print("=" * 60)
    print("Testing Feature Flag Toggling System")
    print("=" * 60)
    
    # Ensure config file exists
    print("\n1. Ensuring config file exists...")
    ensure_config_file()
    print("   [OK] Config file ready")
    
    # Get initial state
    print("\n2. Getting initial feature states...")
    initial_features = get_all_features()
    for name, data in initial_features.items():
        status = "ENABLED" if data['enabled'] else "DISABLED"
        print(f"   - {name}: {status}")
    
    # Test reading feature flags
    print("\n3. Testing is_feature_enabled()...")
    test_features = ['face_recognition', 'legacy_analytics', 'maintenance_mode']
    for feature in test_features:
        enabled = is_feature_enabled(feature)
        print(f"   - {feature}: {enabled}")
    
    # Test toggling a feature
    print("\n4. Testing toggle_feature()...")
    test_feature = 'face_recognition'
    initial_state = is_feature_enabled(test_feature)
    print(f"   Initial state of {test_feature}: {initial_state}")
    
    # Toggle ON
    print(f"   Toggling {test_feature} ON...")
    result = toggle_feature(test_feature, True)
    if result:
        new_state = is_feature_enabled(test_feature)
        print(f"   [OK] Toggle successful: {new_state}")
        if new_state != True:
            print(f"   [ERROR] Expected True, got {new_state}")
    else:
        print(f"   [ERROR] Toggle failed")
    
    # Toggle OFF
    print(f"   Toggling {test_feature} OFF...")
    result = toggle_feature(test_feature, False)
    if result:
        new_state = is_feature_enabled(test_feature)
        print(f"   [OK] Toggle successful: {new_state}")
        if new_state != False:
            print(f"   [ERROR] Expected False, got {new_state}")
    else:
        print(f"   [ERROR] Toggle failed")
    
    # Restore initial state
    print(f"   Restoring initial state ({initial_state})...")
    toggle_feature(test_feature, initial_state)
    print(f"   [OK] Restored")
    
    # Test get_all_features
    print("\n5. Testing get_all_features()...")
    all_features = get_all_features()
    print(f"   Found {len(all_features)} features:")
    for name, data in all_features.items():
        status = "ENABLED" if data['enabled'] else "DISABLED"
        print(f"   - {name}: {status} (updated: {data['last_updated']})")
    
    # Verify CSV file
    print("\n6. Verifying CSV file structure...")
    try:
        df = pd.read_csv('data/system_config.csv')
        print(f"   [OK] CSV file readable")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Rows: {len(df)}")
        print(f"   Sample data:")
        print(df.to_string(index=False))
    except Exception as e:
        print(f"   [ERROR] reading CSV: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == '__main__':
    test_feature_toggles()

