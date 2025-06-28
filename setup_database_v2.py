#!/usr/bin/env python3
"""
Setup Supabase database tables for the tutor dashboard
This version creates tables through the Supabase dashboard SQL editor
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import hashlib

# Load environment variables
load_dotenv()

def create_admin_user():
    """Create a default admin user"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Supabase credentials not found in .env file")
        return False
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("SUCCESS: Connected to Supabase")
        
        # Hash password (simple hash for demo - in production use proper hashing)
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        
        try:
            # Try to create the admin user
            response = supabase.table('users').insert({
                'email': 'admin@tutordashboard.com',
                'password_hash': password_hash,
                'role': 'admin',
                'full_name': 'System Administrator'
            }).execute()
            
            print("SUCCESS: Default admin user created")
            print("  Email: admin@tutordashboard.com")
            print("  Password: admin123")
            print("  Role: admin")
            return True
            
        except Exception as e:
            if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
                print("INFO: Admin user already exists")
                return True
            else:
                print(f"ERROR: Could not create admin user: {e}")
                return False
        
    except Exception as e:
        print(f"ERROR: Connection failed: {e}")
        return False

def test_database():
    """Test database connection and tables"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Supabase credentials not found in .env file")
        return False
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # Test users table
        users_response = supabase.table('users').select('*').limit(1).execute()
        print(f"SUCCESS: Users table accessible ({len(users_response.data)} users found)")
        
        # List existing users
        if users_response.data:
            print("Existing users:")
            for user in users_response.data:
                print(f"  - {user.get('email')} ({user.get('role')})")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Database test failed: {e}")
        return False

def print_sql_instructions():
    """Print SQL instructions for manual setup"""
    
    print("\n" + "="*60)
    print("MANUAL DATABASE SETUP INSTRUCTIONS")
    print("="*60)
    print("\nSince automatic table creation failed, please:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Run the following SQL commands:")
    print("\n" + "-"*40)
    print("-- Create users table")
    print("""CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'tutor',
    tutor_id VARCHAR(50),
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""")
    
    print("\n-- Create audit_logs table")
    print("""CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(255) NOT NULL,
    details TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);""")
    
    print("\n-- Insert default admin user")
    password_hash = hashlib.sha256("admin123".encode()).hexdigest()
    print(f"""INSERT INTO users (email, password_hash, role, full_name) 
VALUES ('admin@tutordashboard.com', '{password_hash}', 'admin', 'System Administrator')
ON CONFLICT (email) DO NOTHING;""")
    
    print("\n" + "-"*40)
    print("4. After running the SQL, run this script again to test")
    print("5. Login credentials will be:")
    print("   Email: admin@tutordashboard.com")
    print("   Password: admin123")

if __name__ == "__main__":
    print("=== SUPABASE DATABASE SETUP ===")
    
    print("\n1. Testing database connection...")
    test_success = test_database()
    
    if test_success:
        print("\n2. Creating admin user...")
        admin_success = create_admin_user()
        
        if admin_success:
            print("\n=== SETUP COMPLETE ===")
            print("Database is ready for use!")
            print("\nYou can now:")
            print("1. Run the Flask application: python app.py")
            print("2. Login with admin@tutordashboard.com / admin123")
            print("3. Create additional users through the admin panel")
        else:
            print("\n=== PARTIAL SUCCESS ===")
            print("Database tables exist but admin user creation failed")
            print_sql_instructions()
    else:
        print("\n=== SETUP REQUIRED ===")
        print("Database tables need to be created manually")
        print_sql_instructions()