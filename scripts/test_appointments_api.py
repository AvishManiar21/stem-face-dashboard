"""Test appointments API endpoint"""
import pandas as pd
import os
import json

APPOINTMENTS_FILE = 'data/core/appointments.csv'

print("Testing Appointments API...")
print("=" * 60)

# Check if file exists
if not os.path.exists(APPOINTMENTS_FILE):
    print("❌ Appointments file not found!")
    exit(1)

print(f"✓ Appointments file exists: {APPOINTMENTS_FILE}")

# Try to read CSV
try:
    df = pd.read_csv(APPOINTMENTS_FILE)
    print(f"✓ CSV read successfully: {len(df)} rows")
    
    if df.empty:
        print("⚠️  CSV is empty")
    else:
        print(f"✓ Columns: {list(df.columns)[:5]}...")
        
        # Test conversion to dict
        df = df.where(pd.notnull(df), None)
        appointments = df.to_dict('records')
        
        # Test JSON serialization
        try:
            json_str = json.dumps(appointments[:1], default=str)  # Test with first record
            print("✓ JSON serialization successful")
        except Exception as e:
            print(f"❌ JSON serialization failed: {e}")
            
        print(f"✓ Converted to {len(appointments)} appointment records")
        
except Exception as e:
    print(f"❌ Error reading CSV: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
print("Test complete!")

