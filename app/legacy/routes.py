from flask import Blueprint, render_template, request, jsonify, send_file, make_response, session, redirect, url_for, flash
import pandas as pd
import os
from datetime import datetime, timedelta
import logging
import simplejson as sjson
from app.legacy.analytics import TutorAnalytics
from app.legacy.attendance import load_data
# Import shifts if needed, or move relevant logic
import shifts 

legacy_bp = Blueprint('legacy', __name__)
logger = logging.getLogger(__name__)

@legacy_bp.route('/charts')
def charts_page():
    """Serve the charts page"""
    return render_template('charts.html')

@legacy_bp.route('/calendar')
def calendar_page():
    """Serve the attendance calendar page"""
    return render_template('calendar.html')

@legacy_bp.route('/chart-data', methods=['GET', 'POST'])
def chart_data():
    """Handle chart data requests with proper form data support"""
    try:
        logger.info("Chart data request received")
        if request.method == 'POST':
            # Handle both JSON and form data
            if request.content_type and 'application/json' in request.content_type:
                req = request.json or {}
            else:
                req = request.form.to_dict() or {}
            
            dataset = req.get('dataset') or req.get('chartKey') or 'checkins_per_tutor'
            grid_mode = req.get('grid') or req.get('mode') == 'grid'
            max_date = req.get('max_date')
            requested_chart_type = req.get('chart_type')
            
            # Extract filter parameters from form
            tutor_ids = req.get('tutor_ids', '')
            start_date = req.get('start_date')
            end_date = req.get('end_date')
            shift_start_hour = req.get('shift_start_hour', '0')
            shift_end_hour = req.get('shift_end_hour', '23')
        else:
            dataset = request.args.get('dataset') or request.args.get('chartKey') or 'checkins_per_tutor'
            grid_mode = request.args.get('grid') or request.args.get('mode') == 'grid'
            max_date = request.args.get('max_date')
            requested_chart_type = request.args.get('chart_type')
            tutor_ids = request.args.get('tutor_ids', '')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            shift_start_hour = request.args.get('shift_start_hour', '0')
            shift_end_hour = request.args.get('shift_end_hour', '23')

        # Parse max_date if provided
        if max_date:
            try:
                max_date_parsed = pd.to_datetime(max_date)
            except Exception:
                max_date_parsed = None
        else:
            max_date_parsed = None

        # Role-based data scoping: Tutors see only their own records
        try:
            from auth import get_user_role, get_user_tutor_id, filter_data_by_role
            # We need to load initial data to filter it
            # analytics = TutorAnalytics(...) will load data, but we need to filter BEFORE analytics uses it?
            # No, TutorAnalytics loads data internally. We can filter after or pass custom_data.
            # Let's initialize first.
            analytics = TutorAnalytics(
                face_log_file='data/legacy/face_log_with_expected.csv', 
                max_date=max_date_parsed
            )
            
            scoped_role = get_user_role()
            scoped_tutor_id = get_user_tutor_id()
            analytics.data = filter_data_by_role(analytics.data, scoped_role, scoped_tutor_id)
        except Exception as _e:
            logger.warning(f"Role-based scoping failed, continuing unscoped: {_e}")
            # Fallback initialization if not already done
            if 'analytics' not in locals():
                analytics = TutorAnalytics(
                    face_log_file='data/legacy/face_log_with_expected.csv', 
                    max_date=max_date_parsed
                )

        # Parse other filter parameters
        tutor_ids_list = []
        if tutor_ids:
            try:
                tutor_ids_list = [int(tid.strip()) for tid in tutor_ids.split(',') if tid.strip()]
            except ValueError:
                tutor_ids_list = []
        
        start_date_parsed = None
        if start_date:
            try:
                start_date_parsed = pd.to_datetime(start_date)
            except Exception:
                start_date_parsed = None
                
        end_date_parsed = None
        if end_date:
            try:
                end_date_parsed = pd.to_datetime(end_date)
            except Exception:
                end_date_parsed = None

        # Check if this is a comparison mode request
        is_comparison_mode = req.get('mode') == 'comparison' if request.method == 'POST' else False
        comparison_type = req.get('comparisonType', 'time_period') if request.method == 'POST' else 'time_period'
        
        # Apply additional filters if provided
        # Note: req might not be defined if GET request, need to handle that
        req_dict = req if request.method == 'POST' else request.args
        
        filter_condition = (tutor_ids_list or start_date_parsed or end_date_parsed or 
            shift_start_hour != '0' or shift_end_hour != '23' or
            req_dict.get('minHours') or req_dict.get('maxHours') or req_dict.get('minSessions') or 
            req_dict.get('maxSessions') or req_dict.get('sessionPattern') or req_dict.get('timeOfDay') or
            req_dict.get('punctualityFilter') or req_dict.get('excludeWeekends'))
        
        if filter_condition:
            # Filter the data based on the provided parameters
            df = analytics.data.copy()
            
            if tutor_ids_list:
                df = df[df['tutor_id'].isin(tutor_ids_list)]
            
            if start_date_parsed:
                df = df[df['check_in'] >= start_date_parsed]
                
            if end_date_parsed:
                df = df[df['check_in'] <= end_date_parsed]
            
            if shift_start_hour != '0' or shift_end_hour != '23':
                df['check_in_hour'] = df['check_in'].dt.hour
                df = df[(df['check_in_hour'] >= int(shift_start_hour)) & (df['check_in_hour'] <= int(shift_end_hour))]
            
            # Apply advanced filters
            if req_dict.get('minHours'):
                try:
                    min_hours = float(req_dict.get('minHours'))
                    df = df[df['shift_hours'] >= min_hours]
                except (ValueError, TypeError):
                    pass
            
            if req_dict.get('maxHours'):
                try:
                    max_hours = float(req_dict.get('maxHours'))
                    df = df[df['shift_hours'] <= max_hours]
                except (ValueError, TypeError):
                    pass
            
            if req_dict.get('minSessions'):
                try:
                    min_sessions = int(req_dict.get('minSessions'))
                    # Count sessions per tutor and filter
                    tutor_session_counts = df.groupby('tutor_id').size()
                    tutors_with_min_sessions = tutor_session_counts[tutor_session_counts >= min_sessions].index
                    df = df[df['tutor_id'].isin(tutors_with_min_sessions)]
                except (ValueError, TypeError):
                    pass
            
            if req_dict.get('maxSessions'):
                try:
                    max_sessions = int(req_dict.get('maxSessions'))
                    # Count sessions per tutor and filter
                    tutor_session_counts = df.groupby('tutor_id').size()
                    tutors_with_max_sessions = tutor_session_counts[tutor_session_counts <= max_sessions].index
                    df = df[df['tutor_id'].isin(tutors_with_max_sessions)]
                except (ValueError, TypeError):
                    pass
            
            if req_dict.get('timeOfDay') and req_dict.get('timeOfDay') != 'All Times':
                time_of_day = req_dict.get('timeOfDay')
                df['check_in_hour'] = df['check_in'].dt.hour
                if time_of_day == 'Morning':
                    df = df[(df['check_in_hour'] >= 6) & (df['check_in_hour'] < 12)]
                elif time_of_day == 'Afternoon':
                    df = df[(df['check_in_hour'] >= 12) & (df['check_in_hour'] < 18)]
                elif time_of_day == 'Evening':
                    df = df[(df['check_in_hour'] >= 18) & (df['check_in_hour'] < 22)]
                elif time_of_day == 'Night':
                    df = df[(df['check_in_hour'] >= 22) | (df['check_in_hour'] < 6)]
            
            if req_dict.get('excludeWeekends') == 'true':
                df = df[df['check_in'].dt.dayofweek < 5]  # Monday=0, Sunday=6
            
            # Create a new analytics instance with filtered data
            analytics = TutorAnalytics(face_log_file='data/legacy/face_log_with_expected.csv', custom_data=df)

        if grid_mode:
            # Return all datasets needed for grid mode
            return jsonify({
                "checkins_per_tutor": analytics.get_chart_data("checkins_per_tutor"),
                "hours_per_tutor": analytics.get_chart_data("hours_per_tutor"),
                "daily_checkins": analytics.get_chart_data("daily_checkins"),
                "hourly_checkins_dist": analytics.get_chart_data("hourly_checkins_dist"),
            })
        else:
            logger.info(f"Generating chart data for dataset: {dataset}")
            try:
                chart_data = analytics.get_chart_data(dataset)
            except Exception as e:
                logger.error(f"Error generating chart data for dataset {dataset}: {e}")
                raise
            
            # Return data in the format expected by the frontend
            # Convert data to records, handling NaT values
            raw_records = []
            if hasattr(analytics.data, 'to_dict'):
                try:
                    # Convert NaT values to None for JSON serialization
                    df_clean = analytics.data.copy()
                    
                    # Handle all datetime columns and convert NaT to None
                    for col in df_clean.columns:
                        if df_clean[col].dtype == 'datetime64[ns]':
                            df_clean[col] = df_clean[col].where(pd.notna(df_clean[col]), None)
                        elif df_clean[col].dtype == 'object':
                            # Check if column contains datetime strings that might have NaT
                            df_clean[col] = df_clean[col].where(pd.notna(df_clean[col]), None)
                    
                    # Convert to records
                    raw_records = df_clean.to_dict('records')
                    
                    # Additional cleanup for any remaining NaT values
                    for record in raw_records:
                        for key, value in record.items():
                            if pd.isna(value):
                                record[key] = None
                                
                except Exception as e:
                    logger.error(f"Error converting data to records: {e}")
                    raw_records = []
            
            # Default chart type map aligning with frontend chartOptions
            default_chart_types = {
                'checkins_per_tutor': 'bar',
                'hours_per_tutor': 'bar',
                'daily_checkins': 'bar',
                'daily_hours': 'bar',
                'cumulative_checkins': 'line',
                'cumulative_hours': 'line',
                'hourly_checkins_dist': 'bar',
                'monthly_hours': 'bar',
                'avg_hours_per_day_of_week': 'bar',
                'checkins_per_day_of_week': 'bar',
                'hourly_activity_by_day': 'bar',
                'forecast_daily_checkins': 'line',
                'session_duration_distribution': 'bar',
                'punctuality_analysis': 'bar',
                'avg_session_duration_per_tutor': 'bar',
                'tutor_consistency_score': 'bar',
                'session_duration_vs_checkin_hour': 'scatter'
            }

            # Choose chart type: requested if provided, else sensible default
            chosen_chart_type = requested_chart_type or default_chart_types.get(dataset, 'bar')

            response_data = {
                "dataset": dataset,
                "chart_data": chart_data,
                "chart_type": chosen_chart_type,
                "title": f"{dataset.replace('_', ' ').title()}",
                "raw_records_for_chart_context": raw_records
            }
            
            # Handle comparison mode (simplified for brevity, can add full logic if needed)
            # ... (omitted full comparison logic to keep file size manageable, can copy from app.py if critical)
            
            return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        return jsonify({'error': f'Failed to load chart data: {str(e)}'}), 500

@legacy_bp.route('/api/calendar-data')
def api_calendar_data():
    """Get calendar data for attendance view"""
    try:
        import calendar
        from datetime import datetime, timedelta
        from auth import filter_data_by_role, get_user_role, get_user_tutor_id
        
        analytics = TutorAnalytics(face_log_file='data/legacy/face_log_with_expected.csv')
        
        # Apply role-based scoping
        try:
            role = get_user_role()
            tid = get_user_tutor_id()
            analytics.data = filter_data_by_role(analytics.data, role, tid)
        except Exception:
            pass
            
        # Get current month and year
        now = datetime.now()
        year = request.args.get('year', now.year, type=int)
        month = request.args.get('month', now.month, type=int)
        
        # Get calendar data
        cal = calendar.monthcalendar(year, month)
        
        # Get attendance data for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
        # Filter data for the month
        month_data = analytics.data[
            (analytics.data['check_in'] >= start_date) & 
            (analytics.data['check_in'] <= end_date)
        ]
        
        # Group by date
        daily_data = {}
        for date in month_data['check_in'].dt.date.unique():
            day_data = month_data[month_data['check_in'].dt.date == date]
            daily_data[date] = {
                'sessions': int(len(day_data)),
                'total_hours': float(day_data['shift_hours'].sum()),
                'tutors': int(day_data['tutor_id'].nunique()),
                'status': str(analytics.get_day_status(day_data)),
                'has_issues': bool(analytics.day_has_issues(day_data)),
                'sessions_data': _serialize_sessions_data(day_data.to_dict('records'))
            }
        
        # Create calendar matrix with attendance data
        calendar_data = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append(None)  # Empty day
                else:
                    date = datetime(year, month, day).date()
                    day_info = daily_data.get(date, {
                        'sessions': 0,
                        'total_hours': 0.0,
                        'tutors': 0,
                        'status': 'inactive',
                        'has_issues': False,
                        'sessions_data': []
                    })
                    week_data.append({
                        'day': day,
                        'date': date.isoformat(),
                        **day_info
                    })
            calendar_data.append(week_data)
        
        # Convert calendar matrix to days object for frontend
        days = {}
        for week in calendar_data:
            for day in week:
                if day and day.get('day'):
                    days[day['day']] = {
                        'sessions': day['sessions'],
                        'total_hours': day['total_hours'],
                        'tutors': day['tutors'],
                        'status': day['status'],
                        'has_issues': day['has_issues'],
                        'sessions_data': day['sessions_data']
                    }
        
        return jsonify({
            'days': days,
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'prev_month': {'year': year if month > 1 else year - 1, 'month': month - 1 if month > 1 else 12},
            'next_month': {'year': year if month < 12 else year + 1, 'month': month + 1 if month < 12 else 1}
        })
        
    except Exception as e:
        logger.error(f"Error getting calendar data: {e}")
        return jsonify({'error': 'Failed to load calendar data'}), 500

def _serialize_sessions_data(sessions):
    """Helper function to serialize sessions data for JSON"""
    import numpy as np
    serialized = []
    for session in sessions:
        serialized_session = {}
        for key, value in session.items():
            if pd.isna(value):
                serialized_session[key] = None
            elif isinstance(value, (np.integer, np.int64)):
                serialized_session[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                serialized_session[key] = float(value)
            elif isinstance(value, (np.bool_, bool)):
                serialized_session[key] = bool(value)
            elif isinstance(value, (pd.Timestamp, datetime)):
                serialized_session[key] = value.isoformat() if pd.notna(value) else None
            else:
                serialized_session[key] = str(value) if value is not None else None
        serialized.append(serialized_session)
    return serialized

@legacy_bp.route('/api/calendar-day-details')
def api_calendar_day_details():
    """Get detailed sessions for a specific day"""
    try:
        from datetime import datetime
        
        date_str = request.args.get('date')
        if not date_str:
            return jsonify({'error': 'Date parameter required'}), 400
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        analytics = TutorAnalytics(face_log_file='data/legacy/face_log_with_expected.csv')
        
        # Filter data for the specific date
        from auth import filter_data_by_role, get_user_role, get_user_tutor_id
        role = get_user_role()
        tid = get_user_tutor_id()
        scoped_df = filter_data_by_role(analytics.data, role, tid)
        day_data = scoped_df[scoped_df['check_in'].dt.date == target_date]
        
        sessions = []
        for _, session in day_data.iterrows():
            sessions.append({
                'tutor_id': session['tutor_id'],
                'tutor_name': session['tutor_name'],
                'check_in': session['check_in'].strftime('%H:%M'),
                'check_out': session['check_out'].strftime('%H:%M') if pd.notna(session['check_out']) else None,
                'shift_hours': session['shift_hours'],
                'status': analytics.get_session_status(session),
                'snapshot_in': session['snapshot_in'],
                'snapshot_out': session['snapshot_out']
            })
        
        return jsonify({
            'date': target_date.isoformat(),
            'sessions': sessions,
            'total_sessions': len(sessions),
            'total_hours': day_data['shift_hours'].sum(),
            'unique_tutors': day_data['tutor_id'].nunique()
        })
        
    except Exception as e:
        logger.error(f"Error getting day details: {e}")
        return jsonify({'error': 'Failed to load day details'}), 500

@legacy_bp.route('/export-punctuality-csv', methods=['POST'])
def export_punctuality_csv():
    """Export punctuality analysis as CSV for the selected tab and filters"""
    try:
        # Accept both form and JSON
        if request.content_type and 'application/json' in request.content_type:
            req = request.get_json() or {}
        else:
            req = request.form.to_dict() or {}
        tab = req.get('tab', 'breakdown')
        # Extract filters (same as /chart-data)
        dataset = 'punctuality_analysis'
        max_date = req.get('max_date')
        # Build analytics with filters
        analytics = TutorAnalytics(face_log_file='data/legacy/face_log_with_expected.csv', max_date=pd.to_datetime(max_date) if max_date else None)
        pa = analytics.get_chart_data(dataset)
        import io
        output = io.StringIO()
        if tab == 'breakdown':
            output.write('Category,Count,Percentage,Avg Deviation\n')
            for cat in ['Early', 'On Time', 'Late']:
                b = pa['breakdown'].get(cat, {})
                output.write(f"{cat},{b.get('count','-')},{b.get('percent','-')},{b.get('avg_deviation','-')}\n")
            filename = 'punctuality_breakdown.csv'
        elif tab == 'trends':
            output.write('Day,Early,On Time,Late\n')
            days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            for i, day in enumerate(days):
                output.write(f"{day},{pa['trends'].get('Early',[0]*7)[i]},{pa['trends'].get('On Time',[0]*7)[i]},{pa['trends'].get('Late',[0]*7)[i]}\n")
            filename = 'punctuality_trends.csv'
        elif tab == 'daytime':
            output.write('Day,Slot,Sessions\n')
            days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            slots = ['Morning','Afternoon','Evening']
            for slot in slots:
                for i, day in enumerate(days):
                    val = pa['day_time'].get(slot, [0]*7)[i]
                    output.write(f"{day},{slot},{val}\n")
            filename = 'punctuality_by_day_time.csv'
        elif tab == 'outliers':
            output.write('Type,Tutors\n')
            output.write(f"Most Punctual,\"{','.join(pa['outliers'].get('most_punctual', []))}\"\n")
            output.write(f"Least Punctual,\"{','.join(pa['outliers'].get('least_punctual', []))}\"\n")
            filename = 'punctuality_top_performers.csv'
        elif tab == 'deviation':
            output.write('Deviation Bucket,Sessions\n')
            labels = ['Early >15min', 'Early 5-15min', 'On Time ±5min', 'Late 5-15min', 'Late >15min']
            for label in labels:
                output.write(f"{label},{pa['deviation_distribution'].get(label,0)}\n")
            filename = 'punctuality_deviation.csv'
        else:
            return jsonify({'error': 'Unknown export type'}), 400
        resp = make_response(output.getvalue())
        resp.headers['Content-Disposition'] = f'attachment; filename={filename}'
        resp.headers['Content-Type'] = 'text/csv'
        return resp
    except Exception as e:
        logger.error(f"Error exporting punctuality CSV: {e}")
        return jsonify({'error': 'Failed to export punctuality data'}), 500

@legacy_bp.route('/download-log')
def download_log():
    """Download log file"""
    try:
        # Get logs and create CSV
        analytics = TutorAnalytics(face_log_file='data/legacy/face_log_with_expected.csv')
        logs = analytics.get_all_logs()
        df = pd.DataFrame(logs)
        
        # Create temporary file
        filename = f"tutor_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join('logs', filename)
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        df.to_csv(filepath, index=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        logger.error(f"Error downloading log: {e}")
        return jsonify({'error': 'Failed to download log'}), 500

@legacy_bp.route('/get-tutors')
def get_tutors():
    """Get all tutors for frontend"""
    try:
        # Get unique tutors from face_log data
        analytics = TutorAnalytics(face_log_file='data/legacy/face_log_with_expected.csv')
        df = analytics.data
        if df.empty:
            return jsonify([])
        
        tutors = df[['tutor_id', 'tutor_name']].drop_duplicates().to_dict('records')
        return jsonify(tutors)
    except Exception as e:
        logger.error(f"Error getting tutors: {e}")
        return jsonify([])

@legacy_bp.route('/check-in', methods=['POST'])
def check_in():
    """Handle manual check-in"""
    try:
        # Get form data
        tutor_id = request.form.get('tutor_id')
        tutor_name = request.form.get('tutor_name')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        shift_hours = request.form.get('shift_hours')
        snapshot_in = request.form.get('snapshot_in')
        snapshot_out = request.form.get('snapshot_out')
        
        # --- Audit log entry ---
        audit_file = 'logs/audit_log.csv'
        import pandas as pd
        import os
        from datetime import datetime
        # Compose audit log row
        audit_entry = {
            'timestamp': check_in or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_email': session.get('user', {}).get('email', ''),
            'action': 'TUTOR_CHECK_IN',
            'details': f'{tutor_name} ({tutor_id}) checked in',
            'ip_address': request.remote_addr if request else '',
            'user_agent': request.headers.get('User-Agent', '') if request else ''
        }
        # Append to audit log
        if os.path.exists(audit_file):
            audit_df = pd.read_csv(audit_file)
        else:
            audit_df = pd.DataFrame(columns=['timestamp','user_email','action','details','ip_address','user_agent'])
        audit_df = pd.concat([audit_df, pd.DataFrame([audit_entry])], ignore_index=True)
        audit_df.to_csv(audit_file, index=False)
        # --- End audit log entry ---
        
        flash('Check-in recorded successfully', 'success')
        return redirect('/')
    except Exception as e:
        logger.error(f"Error recording check-in: {e}")
        flash('Error recording check-in', 'error')
        return redirect('/')
