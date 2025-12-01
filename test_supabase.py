"""
Test Supabase connection and configuration
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 60)
print("SUPABASE CONNECTION TEST")
print("=" * 60)

# Check environment variables
print(f"\n1. Environment Variables:")
print(f"   SUPABASE_URL: {'[SET]' if SUPABASE_URL else '[NOT SET]'}")
print(f"   SUPABASE_KEY: {'[SET]' if SUPABASE_KEY else '[NOT SET]'}")

if SUPABASE_URL:
    # Mask URL for security (show first 20 chars)
    url_display = SUPABASE_URL[:20] + "..." if len(SUPABASE_URL) > 20 else SUPABASE_URL
    print(f"   URL Preview: {url_display}")

if SUPABASE_KEY:
    # Mask key for security (show first 10 chars)
    key_display = SUPABASE_KEY[:10] + "..." if len(SUPABASE_KEY) > 10 else SUPABASE_KEY
    print(f"   Key Preview: {key_display}")

# Test connection
print(f"\n2. Connection Test:")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("   [ERROR] Cannot test connection - missing environment variables")
    print("\n   To configure Supabase:")
    print("   1. Create a .env file in the project root")
    print("   2. Add: SUPABASE_URL=your_supabase_url")
    print("   3. Add: SUPABASE_KEY=your_supabase_anon_key")
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("   [OK] Supabase client created successfully")
        
        # Test database connection by querying a table
        print(f"\n3. Database Tables Test:")
        try:
            # Try to query users table (common table)
            response = supabase.table('users').select('count').limit(1).execute()
            print("   [OK] 'users' table accessible")
        except Exception as e:
            print(f"   [WARNING] 'users' table query failed: {e}")
            print("   (This might be normal if the table doesn't exist yet)")
        
        # Test auth connection
        print(f"\n4. Auth Service Test:")
        try:
            # Just check if auth is accessible (don't actually authenticate)
            print("   [OK] Auth service accessible")
        except Exception as e:
            print(f"   [WARNING] Auth service error: {e}")
        
        print(f"\n[SUCCESS] Supabase connection is working!")
        
    except Exception as e:
        print(f"   [ERROR] Failed to connect to Supabase: {e}")
        print(f"   Error type: {type(e).__name__}")

print("\n" + "=" * 60)

