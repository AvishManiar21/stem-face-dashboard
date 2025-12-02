"""
Execute SQL to fix RLS policies using Supabase connection
This requires the database connection string from Supabase
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 60)
print("FIXING RLS POLICIES")
print("=" * 60)

# Read the SQL fix file
sql_file = "fix_rls_policies.sql"
try:
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    print(f"\n[OK] Read SQL file: {sql_file}")
except Exception as e:
    print(f"\n[ERROR] Could not read {sql_file}: {e}")
    exit(1)

print("\n" + "=" * 60)
print("MANUAL STEPS REQUIRED")
print("=" * 60)
print("\nSupabase doesn't allow direct SQL execution via API for security.")
print("Please execute the SQL manually:\n")
print("1. Open: https://app.supabase.com/project/tjhcndrxlstezfgiyxla")
print("2. Go to: SQL Editor (left sidebar)")
print("3. Click: New Query")
print("4. Copy the SQL below and paste it:")
print("\n" + "-" * 60)
print(sql_content)
print("-" * 60)
print("\n5. Click: Run (or press Ctrl+Enter)")
print("6. Wait for success message")
print("7. Then run: python import_csv_to_supabase.py")
print("\n" + "=" * 60)

# Also try to provide a direct link if possible
print("\nQuick link to SQL Editor:")
print(f"https://app.supabase.com/project/tjhcndrxlstezfgiyxla/sql/new")

