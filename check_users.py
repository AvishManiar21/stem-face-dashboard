#!/usr/bin/env python3
"""
Check existing users in Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import hashlib

# Load environment variables
load_dotenv()

def check_users():
    """Check all users in Supabase Auth and users table"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Supabase credentials not found in .env file")
        return False
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("✓ Connected to Supabase\n")
        
        # Check Supabase Auth users
        print("=" * 60)
        print("SUPABASE AUTH USERS")
        print("=" * 60)
        try:
            auth_users = supabase.auth.admin.list_users()
            if hasattr(auth_users, 'users') and auth_users.users:
                for user in auth_users.users:
                    print(f"\nEmail: {user.email}")
                    print(f"  ID: {user.id}")
                    print(f"  Metadata: {user.user_metadata}")
                    print(f"  Created: {user.created_at}")
            else:
                print("No users found in Supabase Auth")
        except Exception as e:
            print(f"Could not fetch Supabase Auth users: {e}")
        
        # Check custom users table
        print("\n" + "=" * 60)
        print("CUSTOM USERS TABLE")
        print("=" * 60)
        try:
            response = supabase.table('users').select('*').execute()
            if response.data:
                for user in response.data:
                    print(f"\nEmail: {user.get('email')}")
                    print(f"  ID: {user.get('id')}")
                    print(f"  Role: {user.get('role')}")
                    print(f"  Full Name: {user.get('full_name')}")
                    print(f"  Tutor ID: {user.get('tutor_id')}")
                    print(f"  Has Password Hash: {bool(user.get('password_hash'))}")
                    print(f"  Has Salt: {bool(user.get('salt'))}")
                    print(f"  Created: {user.get('created_at')}")
            else:
                print("No users found in custom users table")
        except Exception as e:
            print(f"Could not fetch custom users table: {e}")
        
        # Test admin credentials
        print("\n" + "=" * 60)
        print("TESTING ADMIN CREDENTIALS")
        print("=" * 60)
        
        test_email = "admin@tutordashboard.com"
        test_password = "admin123"
        
        print(f"\nTesting: {test_email} / {test_password}")
        
        # Try Supabase Auth
        print("\n1. Testing Supabase Auth login...")
        try:
            response = supabase.auth.sign_in_with_password({
                "email": test_email,
                "password": test_password
            })
            if response.user:
                print("   ✓ SUCCESS: Supabase Auth login works!")
                print(f"   User ID: {response.user.id}")
                print(f"   Metadata: {response.user.user_metadata}")
                supabase.auth.sign_out()
            else:
                print("   ✗ FAILED: No user returned")
        except Exception as e:
            print(f"   ✗ FAILED: {e}")
        
        # Try custom users table
        print("\n2. Testing custom users table login...")
        try:
            response = supabase.table('users').select('*').eq('email', test_email).execute()
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                print(f"   ✓ User found in custom table")
                print(f"   Role: {user_data.get('role')}")
                
                # Test password hash
                password_hash = user_data.get('password_hash', '')
                salt = user_data.get('salt', '')
                
                if salt:
                    print("   Using salt-based password verification...")
                    # Would need to implement proper verification here
                else:
                    print("   Using simple SHA-256 hash...")
                    simple_hash = hashlib.sha256(test_password.encode()).hexdigest()
                    if simple_hash == password_hash:
                        print("   ✓ Password hash matches!")
                    else:
                        print(f"   ✗ Password hash mismatch")
                        print(f"   Expected: {password_hash}")
                        print(f"   Got: {simple_hash}")
            else:
                print("   ✗ User not found in custom table")
        except Exception as e:
            print(f"   ✗ FAILED: {e}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    check_users()
