"""
WCOnline-style Scheduling System
Main scheduling module when face recognition is disabled
"""
from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime, timedelta
import pandas as pd
import os
import logging

scheduling_bp = Blueprint('scheduling', __name__)
logger = logging.getLogger(__name__)

# Data paths
APPOINTMENTS_FILE = 'data/core/appointments.csv'
TUTORS_FILE = 'data/core/tutors.csv'
COURSES_FILE = 'data/core/courses.csv'
AVAILABILITY_FILE = 'data/core/availability.csv'

def ensure_data_files():
    """Ensure data files exist"""
    os.makedirs('data/core', exist_ok=True)
    
    if not os.path.exists(APPOINTMENTS_FILE):
        df = pd.DataFrame(columns=[
            'appointment_id', 'student_name', 'student_email', 'tutor_id', 'tutor_name',
            'course_id', 'course_name', 'appointment_date', 'appointment_time',
            'duration', 'status', 'notes', 'created_at', 'updated_at'
        ])
        df.to_csv(APPOINTMENTS_FILE, index=False)
    
    if not os.path.exists(TUTORS_FILE):
        df = pd.DataFrame(columns=[
            'tutor_id', 'name', 'email', 'phone', 'courses', 'active'
        ])
        df.to_csv(TUTORS_FILE, index=False)
    
    if not os.path.exists(COURSES_FILE):
        df = pd.DataFrame(columns=[
            'course_id', 'course_code', 'course_name', 'department', 'active'
        ])
        df.to_csv(COURSES_FILE, index=False)
    
    if not os.path.exists(AVAILABILITY_FILE):
        df = pd.DataFrame(columns=[
            'availability_id', 'tutor_id', 'day_of_week', 'start_time', 'end_time', 'active'
        ])
        df.to_csv(AVAILABILITY_FILE, index=False)

@scheduling_bp.route('/')
def index():
    """Main scheduling dashboard"""
    ensure_data_files()
    return render_template('scheduling/dashboard.html')

@scheduling_bp.route('/appointments')
def appointments():
    """View and manage appointments"""
    ensure_data_files()
    return render_template('scheduling/appointments.html')

@scheduling_bp.route('/tutors')
def tutors():
    """View and manage tutors"""
    ensure_data_files()
    return render_template('scheduling/tutors.html')

@scheduling_bp.route('/courses')
def courses():
    """View and manage courses"""
    ensure_data_files()
    return render_template('scheduling/courses.html')

@scheduling_bp.route('/availability')
def availability():
    """View and manage tutor availability"""
    ensure_data_files()
    return render_template('scheduling/availability.html')

# API Routes
@scheduling_bp.route('/api/appointments', methods=['GET'])
def get_appointments():
    """Get all appointments"""
    try:
        ensure_data_files()
        df = pd.read_csv(APPOINTMENTS_FILE)
        if df.empty:
            return jsonify({'appointments': []})
        
        # Convert to list of dicts
        appointments = df.to_dict('records')
        return jsonify({'appointments': appointments})
    except Exception as e:
        logger.error(f"Error getting appointments: {e}")
        return jsonify({'error': str(e)}), 500

@scheduling_bp.route('/api/appointments', methods=['POST'])
def create_appointment():
    """Create a new appointment"""
    try:
        ensure_data_files()
        data = request.get_json()
        
        # Load existing appointments
        df = pd.read_csv(APPOINTMENTS_FILE)
        
        # Create new appointment
        appointment_id = f"APT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        new_appointment = {
            'appointment_id': appointment_id,
            'student_name': data.get('student_name'),
            'student_email': data.get('student_email'),
            'tutor_id': data.get('tutor_id'),
            'tutor_name': data.get('tutor_name'),
            'course_id': data.get('course_id'),
            'course_name': data.get('course_name'),
            'appointment_date': data.get('appointment_date'),
            'appointment_time': data.get('appointment_time'),
            'duration': data.get('duration', 60),
            'status': 'scheduled',
            'notes': data.get('notes', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        df = pd.concat([df, pd.DataFrame([new_appointment])], ignore_index=True)
        df.to_csv(APPOINTMENTS_FILE, index=False)
        
        return jsonify({'success': True, 'appointment_id': appointment_id})
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        return jsonify({'error': str(e)}), 500

@scheduling_bp.route('/api/tutors', methods=['GET'])
def get_tutors():
    """Get all tutors"""
    try:
        ensure_data_files()
        df = pd.read_csv(TUTORS_FILE)
        if df.empty:
            return jsonify({'tutors': []})
        
        tutors = df[df['active'] == True].to_dict('records') if 'active' in df.columns else df.to_dict('records')
        return jsonify({'tutors': tutors})
    except Exception as e:
        logger.error(f"Error getting tutors: {e}")
        return jsonify({'error': str(e)}), 500

@scheduling_bp.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all courses"""
    try:
        ensure_data_files()
        df = pd.read_csv(COURSES_FILE)
        if df.empty:
            return jsonify({'courses': []})
        
        courses = df[df['active'] == True].to_dict('records') if 'active' in df.columns else df.to_dict('records')
        return jsonify({'courses': courses})
    except Exception as e:
        logger.error(f"Error getting courses: {e}")
        return jsonify({'error': str(e)}), 500

