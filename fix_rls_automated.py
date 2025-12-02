"""
Automated script to fix RLS policies in Supabase
This script uses the Supabase REST API to execute SQL
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    exit(1)

# Note: This requires the service_role key, not the anon key
# For security, we'll try with the current key first
print("=" * 60)
print("FIXING RLS POLICIES IN SUPABASE")
print("=" * 60)
print(f"\nSupabase URL: {SUPABASE_URL[:30]}...")
print("\nAttempting to fix RLS policies...")

# SQL commands to fix RLS
sql_commands = [
    "DROP POLICY IF EXISTS \"Users can view own profile\" ON users;",
    "DROP POLICY IF EXISTS \"Users can view relevant appointments\" ON appointments;",
    "ALTER TABLE users DISABLE ROW LEVEL SECURITY;",
    "ALTER TABLE appointments DISABLE ROW LEVEL SECURITY;"
]

# Try using Supabase Management API (requires service_role key)
# If you have service_role key, add it to .env as SUPABASE_SERVICE_KEY
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", SUPABASE_KEY)

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json"
}

success_count = 0
for i, sql in enumerate(sql_commands, 1):
    try:
        # Use PostgREST RPC if available, or try direct SQL execution
        # Note: Supabase doesn't expose direct SQL execution via REST API for security
        # This is a workaround attempt
        print(f"\n[{i}/{len(sql_commands)}] Executing: {sql[:50]}...")
        
        # Try using the Supabase REST API with a function call
        # This won't work directly, so we'll provide instructions instead
        print("   [INFO] Direct SQL execution via API is not available for security reasons.")
        print("   [INFO] Please run the SQL manually in Supabase Dashboard.")
        
    except Exception as e:
        print(f"   [ERROR] {e}")

print("\n" + "=" * 60)
print("AUTOMATED FIX NOT POSSIBLE")
print("=" * 60)
print("\nSupabase doesn't allow direct SQL execution via the REST API")
print("for security reasons. Please fix RLS policies manually:\n")
print("1. Go to: https://app.supabase.com")
print("2. Select your project: stem-face-dashboard")
print("3. Go to: SQL Editor → New Query")
print("4. Copy and paste the SQL from: fix_rls_policies.sql")
print("5. Click: Run")
print("\nAfter that, re-run: python import_csv_to_supabase.py")
print("=" * 60)

