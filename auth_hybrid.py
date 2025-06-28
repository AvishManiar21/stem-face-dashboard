"""
Hybrid Authentication module - works with both Supabase Auth and custom users table
"""

import os
import hashlib
from functools import wraps
from flask import session, request, jsonify, redirect, url_for, flash
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL and Key must be set in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

def authenticate_user_hybrid(email, password):
    """
    Hybrid authentication - tries Supabase Auth first, then custom users table
    """
    # First try Supabase Auth
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Store user in session
            session['user'] = {
                'id': response.user.id,
                'email': response.user.email,
                'user_metadata': response.user.user_metadata or {}
            }
            session['access_token'] = response.session.access_token
            return True, "Login successful (Supabase Auth)"
            
    except Exception as supabase_error:
        print(f"Supabase Auth failed: {supabase_error}")
        
        # If Supabase Auth fails, try custom users table
        try:
            # Hash the provided password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Query custom users table
            response = supabase.table('users').select('*').eq('email', email).eq('password_hash', password_hash).execute()
            
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                
                # Store user in session (mimicking Supabase Auth format)
                session['user'] = {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'user_metadata': {
                        'role': user_data.get('role', 'tutor'),
                        'full_name': user_data.get('full_name', ''),
                        'tutor_id': user_data.get('tutor_id')
                    }
                }
                return True, "Login successful (Custom Auth)"
            else:
                return False, "Invalid email or password"
                
        except Exception as custom_error:
            print(f"Custom Auth failed: {custom_error}")
            return False, f"Authentication error: {str(custom_error)}"
    
    return False, "Authentication failed"

def test_hybrid_auth():
    """Test the hybrid authentication system"""
    print("Testing hybrid authentication...")
    
    # Test with admin credentials
    success, message = authenticate_user_hybrid("admin@tutordashboard.com", "admin123")
    
    if success:
        print(f"SUCCESS: {message}")
        print(f"Session user: {session.get('user', {})}")
        return True
    else:
        print(f"FAILED: {message}")
        return False

if __name__ == "__main__":
    print("=== TESTING HYBRID AUTHENTICATION ===")
    
    # Initialize Flask session for testing
    from flask import Flask
    app = Flask(__name__)
    app.secret_key = 'test-key'
    
    with app.test_request_context():
        success = test_hybrid_auth()
        
        if success:
            print("\n=== AUTHENTICATION WORKING ===")
            print("You can now use the hybrid authentication system")
        else:
            print("\n=== AUTHENTICATION FAILED ===")
            print("Please check your database setup")