#!/usr/bin/env python3
"""
Create a local admin user in the CSV file for when Supabase is unavailable
"""

import pandas as pd
import hashlib
import os
from datetime import datetime

USERS_FILE = 'logs/users.csv'

def create_local_admin():
    """Create admin user in local CSV file"""
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Admin credentials
    admin_email = "admin@tutordashboard.com"
    admin_password = "admin123"
    
    # Hash password using SHA-256 (matches the auth.py legacy hash)
    password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
    
    # Check if users file exists
    if os.path.exists(USERS_FILE):
        df = pd.read_csv(USERS_FILE)
        
        # Check if admin already exists
        if admin_email in df['email'].values:
            print(f"✓ Admin user already exists: {admin_email}")
            
            # Update the password hash just in case
            df.loc[df['email'] == admin_email, 'password_hash'] = password_hash
            df.loc[df['email'] == admin_email, 'active'] = True
            df.to_csv(USERS_FILE, index=False)
            print("✓ Updated admin password hash")
        else:
            # Add new admin user
            new_admin = {
                'user_id': 'ADMIN001',
                'email': admin_email,
                'full_name': 'System Administrator',
                'role': 'admin',
                'created_at': datetime.now().isoformat(),
                'last_login': '',
                'active': True,
                'password_hash': password_hash
            }
            df = pd.concat([df, pd.DataFrame([new_admin])], ignore_index=True)
            df.to_csv(USERS_FILE, index=False)
            print(f"✓ Created new admin user: {admin_email}")
    else:
        # Create new users file with admin
        df = pd.DataFrame([{
            'user_id': 'ADMIN001',
            'email': admin_email,
            'full_name': 'System Administrator',
            'role': 'admin',
            'created_at': datetime.now().isoformat(),
            'last_login': '',
            'active': True,
            'password_hash': password_hash
        }])
        df.to_csv(USERS_FILE, index=False)
        print(f"✓ Created users file with admin user: {admin_email}")
    
    print("\n" + "=" * 60)
    print("LOCAL ADMIN USER READY")
    print("=" * 60)
    print(f"Email: {admin_email}")
    print(f"Password: {admin_password}")
    print(f"Password Hash: {password_hash}")
    print("\nYou can now login with these credentials!")
    print("The app will use local CSV authentication while Supabase is down.")
    print("=" * 60)

if __name__ == "__main__":
    create_local_admin()
