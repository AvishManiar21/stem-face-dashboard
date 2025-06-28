#!/usr/bin/env python3
"""
Create admin user in Supabase Auth system
This script creates the user in Supabase's authentication system, not just the custom users table
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def create_supabase_auth_user():
    """Create admin user in Supabase Auth system"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Supabase credentials not found in .env file")
        return False
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("SUCCESS: Connected to Supabase")
        
        # Create user in Supabase Auth system
        try:
            response = supabase.auth.admin.create_user({
                "email": "admin@tutordashboard.com",
                "password": "admin123",
                "user_metadata": {
                    "role": "admin",
                    "full_name": "System Administrator"
                },
                "email_confirm": True  # Auto-confirm email
            })
            
            if response.user:
                print("SUCCESS: Admin user created in Supabase Auth")
                print("  Email: admin@tutordashboard.com")
                print("  Password: admin123")
                print("  Role: admin")
                print(f"  User ID: {response.user.id}")
                return True
            else:
                print("ERROR: Failed to create user in Supabase Auth")
                return False
                
        except Exception as e:
            if "already been registered" in str(e).lower() or "already exists" in str(e).lower():
                print("INFO: Admin user already exists in Supabase Auth")
                return True
            else:
                print(f"ERROR: Could not create admin user in Supabase Auth: {e}")
                return False
        
    except Exception as e:
        print(f"ERROR: Connection failed: {e}")
        return False

def test_authentication():
    """Test authentication with the created user"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # Try to authenticate
        response = supabase.auth.sign_in_with_password({
            "email": "admin@tutordashboard.com",
            "password": "admin123"
        })
        
        if response.user:
            print("SUCCESS: Authentication test passed")
            print(f"  User ID: {response.user.id}")
            print(f"  Email: {response.user.email}")
            print(f"  Metadata: {response.user.user_metadata}")
            
            # Sign out after test
            supabase.auth.sign_out()
            return True
        else:
            print("ERROR: Authentication test failed")
            return False
            
    except Exception as e:
        print(f"ERROR: Authentication test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== SUPABASE AUTH USER CREATION ===")
    
    print("\n1. Creating admin user in Supabase Auth...")
    create_success = create_supabase_auth_user()
    
    if create_success:
        print("\n2. Testing authentication...")
        auth_success = test_authentication()
        
        if auth_success:
            print("\n=== SETUP COMPLETE ===")
            print("Authentication is working!")
            print("\nYou can now:")
            print("1. Run the Flask application: python app.py")
            print("2. Login with admin@tutordashboard.com / admin123")
            print("3. Access the dashboard and admin features")
        else:
            print("\n=== AUTHENTICATION ISSUE ===")
            print("User was created but authentication test failed")
            print("Please check your Supabase configuration")
    else:
        print("\n=== CREATION FAILED ===")
        print("Could not create admin user in Supabase Auth")
        print("Please check your Supabase service key permissions")