import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration with feature flags"""
    
    # Flask config
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Feature Flags (OFF by default)
    ENABLE_FACE_RECOGNITION = os.getenv('ENABLE_FACE_RECOGNITION', 'false').lower() == 'true'
    ENABLE_LEGACY_ANALYTICS = os.getenv('ENABLE_LEGACY_ANALYTICS', 'false').lower() == 'true'
    MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true'
    
    # Data paths
    DATA_DIR = 'data/core'
    LEGACY_DATA_DIR = 'data/legacy'
    USERS_FILE = 'data/core/users.csv'
    TUTORS_FILE = 'data/core/tutors.csv'
    COURSES_FILE = 'data/core/courses.csv'
    AVAILABILITY_FILE = 'data/core/availability.csv'
    APPOINTMENTS_FILE = 'data/core/appointments.csv'
    AUDIT_LOG_FILE = 'logs/audit_log.csv'
    
    # Legacy data paths
    LEGACY_FACE_LOG = 'data/legacy/face_log.csv'
    LEGACY_SHIFTS = 'data/legacy/shifts.csv'
    
    # Roles
    ROLES = ['admin', 'tutor']
    ROLE_HIERARCHY = {
        'tutor': 1,
        'admin': 2
    }
