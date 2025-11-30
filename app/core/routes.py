from flask import Blueprint, render_template, request, jsonify, send_file, make_response
import logging
from pathlib import Path
import pandas as pd

# Import new core analytics
from app.core.analytics import SchedulingAnalytics

from app.auth.service import login_required 

analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)

@analytics_bp.route('/charts')
@login_required
def charts_page():
    """Serve the charts page"""
    return render_template('charts.html')

@analytics_bp.route('/calendar')
@login_required
def calendar_page():
    """Serve the attendance calendar page"""
    return render_template('calendar.html')

@analytics_bp.route('/chart-data', methods=['GET', 'POST'])
def chart_data():
    """Handle chart data requests for appointment/scheduling system"""
    try:
        logger.info("Chart data request received")
        
        # Get request parameters
        if request.method == 'POST':
            if request.content_type and 'application/json' in request.content_type:
                req = request.json or {}
            else:
                req = request.form.to_dict() or {}
        else:
            req = request.args.to_dict() or {}
        
        dataset = req.get('dataset', 'appointments_per_tutor')
        chart_type = req.get('chart_type', 'bar')
        mode = req.get('mode', 'single')
        
        # Initialize analytics
        analytics = SchedulingAnalytics(data_dir='data/core')
        
        # Prepare filters
        filters = {}
        if req.get('tutor_ids'):
            filters['tutor_ids'] = req.get('tutor_ids')
        if req.get('start_date'):
            filters['start_date'] = req.get('start_date')
        if req.get('end_date'):
            filters['end_date'] = req.get('end_date')
        if req.get('status'):
            filters['status'] = req.get('status')
        if req.get('course_ids'):
            filters['course_ids'] = req.get('course_ids')
        
        # Handle grid mode - return multiple datasets for 6 charts
        if mode == 'grid':
            return jsonify({
                "appointments_per_tutor": analytics.get_chart_data("appointments_per_tutor", **filters),
                "hours_per_tutor": analytics.get_chart_data("hours_per_tutor", **filters),
                "daily_appointments": analytics.get_chart_data("daily_appointments", **filters),
                "appointments_by_status": analytics.get_chart_data("appointments_by_status", **filters),
                "course_popularity": analytics.get_chart_data("course_popularity", **filters),
                "hourly_appointments_dist": analytics.get_chart_data("hourly_appointments_dist", **filters),
            })
        
        # Get chart data
        chart_data_result = analytics.get_chart_data(dataset, **filters)
        
        # Get summary stats
        summary_stats = analytics.get_summary_stats(**filters)
        
        # Dataset titles
        titles = {
            'appointments_per_tutor': 'Appointments per Tutor',
            'hours_per_tutor': 'Scheduled Hours per Tutor',
            'daily_appointments': 'Daily Appointments',
            'daily_hours': 'Daily Scheduled Hours',
            'appointments_by_status': 'Appointments by Status',
            'appointments_by_course': 'Appointments by Course',
            'appointments_per_day_of_week': 'Appointments per Day of Week',
            'hourly_appointments_dist': 'Appointments by Hour',
            'avg_appointment_duration': 'Average Appointment Duration',
            'tutor_workload': 'Tutor Workload (Total Hours)',
            'course_popularity': 'Course Popularity',
            'monthly_appointments': 'Monthly Appointments',
            'tutor_availability_hours': 'Tutor Available Hours',
            'shift_coverage': 'Shift Coverage',
            'appointment_trends': 'Appointment Trends'
        }
        
        # Prepare response
        response = {
            'chart_data': chart_data_result,
            'chart_type': chart_type,
            'title': titles.get(dataset, dataset.replace('_', ' ').title()),
            'dataset': dataset,
            'summary': summary_stats
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing chart data: {e}", exc_info=True)
        return jsonify({'error': str(e), 'chart_data': {}}), 500

@analytics_bp.route('/get-tutors', methods=['GET'])
def get_tutors():
    """Get list of all tutors"""
    try:
        analytics = SchedulingAnalytics(data_dir='data/core')
        tutors_list = []
        
        if not analytics.tutors.empty:
            for _, tutor in analytics.tutors.iterrows():
                tutors_list.append({
                    'tutor_id': tutor['tutor_id'],
                    'tutor_name': tutor.get('full_name', f"Tutor {tutor['tutor_id']}")
                })
        
        return jsonify(tutors_list)
    except Exception as e:
        logger.error(f"Error getting tutors: {e}")
        return jsonify([])

@analytics_bp.route('/get-courses', methods=['GET'])
def get_courses():
    """Get list of all courses"""
    try:
        analytics = SchedulingAnalytics(data_dir='data/core')
        courses_list = []
        
        if not analytics.courses.empty:
            for _, course in analytics.courses.iterrows():
                courses_list.append({
                    'course_id': course['course_id'],
                    'course_code': course.get('course_code', ''),
                    'course_name': course.get('course_name', f"Course {course['course_id']}")
                })
        
        return jsonify(courses_list)
    except Exception as e:
        logger.error(f"Error getting courses: {e}")
        return jsonify([])

@analytics_bp.route('/api/calendar-data', methods=['GET'])
def api_calendar_data():
    """Get calendar data for a specific month"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        if not year or not month:
            return jsonify({'error': 'Year and month are required'}), 400
        
        analytics = SchedulingAnalytics(data_dir='data/core')
        
        # Get appointments for the month
        appointments = analytics.appointments.copy()
        if not appointments.empty:
            appointments['appointment_date'] = pd.to_datetime(appointments['appointment_date'], errors='coerce')
            month_appointments = appointments[
                (appointments['appointment_date'].dt.year == year) &
                (appointments['appointment_date'].dt.month == month)
            ]
        else:
            month_appointments = pd.DataFrame()
        
        # Group by day of month (1-31)
        days_data = {}
        if not month_appointments.empty:
            # Merge with tutors to get tutor names
            if not analytics.tutors.empty:
                month_appointments = month_appointments.merge(
                    analytics.tutors[['tutor_id', 'full_name']], 
                    on='tutor_id', 
                    how='left'
                )
            
            for date, group in month_appointments.groupby(month_appointments['appointment_date'].dt.date):
                day_num = date.day
                
                # Calculate total hours from start_time and end_time
                total_hours = 0
                for _, appt in group.iterrows():
                    try:
                        if pd.notna(appt.get('start_time')) and pd.notna(appt.get('end_time')):
                            # Parse time strings (format: HH:MM:SS)
                            start_str = str(appt['start_time'])
                            end_str = str(appt['end_time'])
                            
                            # Convert to datetime for calculation
                            from datetime import datetime, timedelta
                            start_time = datetime.strptime(start_str, '%H:%M:%S')
                            end_time = datetime.strptime(end_str, '%H:%M:%S')
                            
                            # Calculate duration in hours
                            duration = (end_time - start_time).total_seconds() / 3600
                            total_hours += duration
                    except Exception as e:
                        logger.warning(f"Could not calculate duration for appointment: {e}")
                        continue
                
                # Determine status based on appointments
                status = 'normal'
                cancelled_count = len(group[group['status'] == 'cancelled']) if 'status' in group.columns else 0
                if cancelled_count > len(group) * 0.3:  # More than 30% cancelled
                    status = 'danger'
                elif cancelled_count > 0:
                    status = 'warning'
                
                # Get unique tutors
                unique_tutors = group['tutor_id'].nunique()
                
                # Prepare session data for modal
                sessions_data = []
                for _, appt in group.iterrows():
                    # Calculate individual session duration
                    duration_hours = 0
                    try:
                        if pd.notna(appt.get('start_time')) and pd.notna(appt.get('end_time')):
                            start_str = str(appt['start_time'])
                            end_str = str(appt['end_time'])
                            from datetime import datetime
                            start_time = datetime.strptime(start_str, '%H:%M:%S')
                            end_time = datetime.strptime(end_str, '%H:%M:%S')
                            duration_hours = (end_time - start_time).total_seconds() / 3600
                    except:
                        pass
                    
                    session = {
                        'tutor_id': appt.get('tutor_id', 'Unknown'),
                        'tutor_name': appt.get('full_name', 'Unknown Tutor'),
                        'start_time': str(appt.get('start_time', '')),
                        'end_time': str(appt.get('end_time', '')),
                        'duration_hours': round(duration_hours, 1),
                        'status': appt.get('status', 'scheduled'),
                        'course_id': appt.get('course_id', ''),
                    }
                    sessions_data.append(session)
                
                days_data[day_num] = {
                    'sessions': len(group),
                    'total_hours': round(total_hours, 1),
                    'status': status,
                    'tutors': unique_tutors,
                    'has_issues': status in ['warning', 'danger'],
                    'sessions_data': sessions_data
                }
        
        return jsonify({
            'year': year,
            'month': month,
            'days': days_data
        })
    except Exception as e:
        logger.error(f"Error getting calendar data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

