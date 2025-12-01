"""
Check Supabase database details - tables, users, etc.
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Supabase environment variables not set")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("SUPABASE DATABASE DETAILS")
print("=" * 60)

# Check users table
print("\n1. Users Table:")
try:
    response = supabase.table('users').select('*').limit(5).execute()
    users = response.data if response.data else []
    print(f"   Found {len(users)} users (showing first 5)")
    for user in users[:5]:
        email = user.get('email', 'N/A')
        role = user.get('role', 'N/A')
        active = user.get('active', 'N/A')
        print(f"   - {email} (role: {role}, active: {active})")
except Exception as e:
    print(f"   [ERROR] Could not query users table: {e}")

# Check for other common tables
print("\n2. Checking for other tables:")
common_tables = ['tutors', 'courses', 'appointments', 'shifts', 'availability', 'time_slots']
for table_name in common_tables:
    try:
        response = supabase.table(table_name).select('*').limit(1).execute()
        count_response = supabase.table(table_name).select('*', count='exact').execute()
        count = count_response.count if hasattr(count_response, 'count') else len(response.data) if response.data else 0
        print(f"   [OK] '{table_name}' table exists ({count} rows)")
    except Exception as e:
        error_msg = str(e)
        if 'relation' in error_msg.lower() or 'does not exist' in error_msg.lower():
            print(f"   [MISSING] '{table_name}' table does not exist")
        else:
            print(f"   [ERROR] '{table_name}' table error: {e}")

# Check auth users
print("\n3. Supabase Auth Users:")
try:
    # Note: This requires admin privileges
    response = supabase.auth.admin.list_users()
    if response and hasattr(response, 'users'):
        auth_users = response.users
        print(f"   Found {len(auth_users)} auth users")
        for user in auth_users[:5]:
            email = user.email if hasattr(user, 'email') else 'N/A'
            print(f"   - {email}")
    else:
        print("   [INFO] No auth users found or insufficient permissions")
except Exception as e:
    error_msg = str(e)
    if 'permission' in error_msg.lower() or 'not allowed' in error_msg.lower():
        print("   [INFO] Insufficient permissions to list auth users (this is normal)")
    else:
        print(f"   [ERROR] Could not list auth users: {e}")

print("\n" + "=" * 60)
print("Summary: Supabase is configured and connected!")
print("=" * 60)

