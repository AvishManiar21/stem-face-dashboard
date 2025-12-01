from flask import Blueprint, render_template, request, jsonify, send_file, make_response
import logging
from pathlib import Path
import pandas as pd

# Import new core analytics
from app.core.analytics import SchedulingAnalytics
from app.core.scheduling_manager import SchedulingManager

from app.auth.service import login_required 

analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)

# Initialize SchedulingManager (singleton instance)
_scheduling_manager = None
_csv_watcher = None

def get_scheduling_manager():
    """Get or create SchedulingManager instance"""
    global _scheduling_manager, _csv_watcher
    if _scheduling_manager is None:
        _scheduling_manager = SchedulingManager(data_dir='data/core')
        
        # Initialize CSV watcher (optional - requires watchdog library)
        try:
            from app.core.csv_watcher import CSVWatcher
            if _csv_watcher is None:
                def reload_callback():
                    """Callback to reload data when CSV files change"""
                    global _scheduling_manager
                    logger.info("Auto-reloading data due to CSV file change...")
                    _scheduling_manager.load_data()
                
                _csv_watcher = CSVWatcher(
                    data_dir='data/core',
                    reload_callback=reload_callback
                )
                
                # Start watching (only if watchdog is available)
                if _csv_watcher.start_watching():
                    logger.info("CSV file watcher started")
                else:
                    logger.info("CSV file watcher not available (install watchdog for auto-reload)")
        except ImportError:
            logger.debug("CSV watcher not available - install watchdog library for auto-reload")
        except Exception as e:
            logger.warning(f"Could not initialize CSV watcher: {e}")
    
    return _scheduling_manager

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
        
        # Prepare filters - collect all filter parameters
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
        if req.get('duration'):
            filters['duration'] = req.get('duration')
        if req.get('day_type'):
            filters['day_type'] = req.get('day_type')
        if req.get('shift_start_hour'):
            filters['shift_start_hour'] = req.get('shift_start_hour')
        if req.get('shift_end_hour'):
            filters['shift_end_hour'] = req.get('shift_end_hour')
        
        logger.info(f"Filters received: {filters}")
        
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

# ============================================================================
# Phase 2: Scheduling API Routes
# ============================================================================

@analytics_bp.route('/api/schedule/week', methods=['GET'])
@login_required
def get_week_schedule():
    """Get weekly schedule grid"""
    try:
        start_date = request.args.get('start_date')
        tutor_ids = request.args.get('tutor_ids')
        
        if not start_date:
            return jsonify({'error': 'start_date parameter is required'}), 400
        
        # Parse tutor_ids if provided (comma-separated)
        tutor_list = None
        if tutor_ids:
            tutor_list = [tid.strip() for tid in tutor_ids.split(',') if tid.strip()]
        
        manager = get_scheduling_manager()
        schedule_data = manager.get_week_schedule(start_date, tutor_list)
        
        return jsonify(schedule_data)
    except Exception as e:
        logger.error(f"Error getting week schedule: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/schedule/available-slots', methods=['GET'])
@login_required
def get_available_slots():
    """Get available time slots for booking"""
    try:
        tutor_id = request.args.get('tutor_id')
        date = request.args.get('date')
        duration = request.args.get('duration', type=float, default=1.0)
        
        if not tutor_id or not date:
            return jsonify({'error': 'tutor_id and date parameters are required'}), 400
        
        manager = get_scheduling_manager()
        slots = manager.get_available_slots(tutor_id, date, duration)
        
        return jsonify({
            'tutor_id': tutor_id,
            'date': date,
            'duration_hours': duration,
            'available_slots': slots
        })
    except Exception as e:
        logger.error(f"Error getting available slots: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/appointments/book', methods=['POST'])
@login_required
def book_appointment():
    """Student books an appointment"""
    try:
        data = request.json or {}
        
        # Required fields
        tutor_id = data.get('tutor_id')
        student_email = data.get('student_email')
        course_id = data.get('course_id')
        date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not all([tutor_id, student_email, course_id, date, start_time, end_time]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: tutor_id, student_email, course_id, date, start_time, end_time'
            }), 400
        
        # Optional fields
        student_name = data.get('student_name')
        notes = data.get('notes', '')
        booking_type = data.get('booking_type', 'student_booked')
        
        manager = get_scheduling_manager()
        result = manager.book_appointment(
            tutor_id=tutor_id,
            student_email=student_email,
            course_id=course_id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            student_name=student_name,
            notes=notes,
            booking_type=booking_type
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error booking appointment: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/appointments/cancel', methods=['POST'])
@login_required
def cancel_appointment():
    """Cancel an appointment"""
    try:
        data = request.json or {}
        appointment_id = data.get('appointment_id')
        
        if not appointment_id:
            return jsonify({
                'success': False,
                'error': 'appointment_id is required'
            }), 400
        
        manager = get_scheduling_manager()
        result = manager.cancel_appointment(appointment_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/appointments/my-appointments', methods=['GET'])
@login_required
def get_my_appointments():
    """Get appointments for logged-in student"""
    try:
        student_email = request.args.get('student_email')
        upcoming_only = request.args.get('upcoming_only', 'true').lower() == 'true'
        
        if not student_email:
            return jsonify({'error': 'student_email parameter is required'}), 400
        
        manager = get_scheduling_manager()
        appointments = manager.get_my_appointments(student_email, upcoming_only)
        
        return jsonify({
            'student_email': student_email,
            'upcoming_only': upcoming_only,
            'appointments': appointments,
            'count': len(appointments)
        })
    except Exception as e:
        logger.error(f"Error getting student appointments: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/admin/reload-data', methods=['POST'])
@login_required
def reload_csv_data():
    """Admin triggers data reload (Option B: Manual Reload)"""
    try:
        global _scheduling_manager
        _scheduling_manager = None  # Reset singleton
        
        manager = get_scheduling_manager()
        
        return jsonify({
            'success': True,
            'message': 'Data reloaded successfully',
            'appointments_count': len(manager.appointments),
            'tutors_count': len(manager.tutors),
            'auto_reload_enabled': _csv_watcher.is_active() if _csv_watcher else False
        })
    except Exception as e:
        logger.error(f"Error reloading data: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

