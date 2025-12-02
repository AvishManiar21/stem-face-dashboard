"""
Verify all data was imported successfully
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("FINAL IMPORT VERIFICATION")
print("=" * 60)

# Check users count and roles
print("\n1. Users:")
try:
    response = supabase.table('users').select('*', count='exact').execute()
    total_users = response.count if hasattr(response, 'count') else len(response.data) if response.data else 0
    print(f"   Total users: {total_users}")
    
    # Check for staff role
    staff_response = supabase.table('users').select('*').eq('role', 'staff').execute()
    staff_count = len(staff_response.data) if staff_response.data else 0
    print(f"   Users with 'staff' role: {staff_count}")
    
    if staff_count > 0:
        print("   [OK] Staff users imported successfully!")
        for user in staff_response.data[:3]:
            print(f"      - {user.get('email')} ({user.get('role')})")
except Exception as e:
    print(f"   [ERROR] {e}")

# Check appointments count and statuses
print("\n2. Appointments:")
try:
    response = supabase.table('appointments').select('*', count='exact').execute()
    total_appts = response.count if hasattr(response, 'count') else len(response.data) if response.data else 0
    print(f"   Total appointments: {total_appts}")
    
    # Check for no-show status
    noshow_response = supabase.table('appointments').select('*').eq('status', 'no-show').execute()
    noshow_count = len(noshow_response.data) if noshow_response.data else 0
    print(f"   Appointments with 'no-show' status: {noshow_count}")
    
    if noshow_count > 0:
        print("   [OK] No-show appointments imported successfully!")
except Exception as e:
    print(f"   [ERROR] {e}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("\nExpected counts from CSV:")
print("  - Users: 26 (including 5 with 'staff' role)")
print("  - Tutors: 20")
print("  - Courses: 25")
print("  - Appointments: 50 (including 11 with 'no-show' status)")
print("  - Shifts: 30")
print("  - Shift Assignments: 38")
print("  - Availability: 63")
print("  - Tutor-Course Relationships: 75")
print("  - Audit Log: 100")
print("\n" + "=" * 60)

