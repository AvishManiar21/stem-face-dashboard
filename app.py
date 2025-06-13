from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for
import pandas as pd
from datetime import datetime, timedelta
import os
import io

app = Flask(__name__)
CSV_FILE = 'logs/face_log.csv'
SNAPSHOTS_DIR = 'static/snapshots'

def load_data():
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty: 
            raise FileNotFoundError 
    except FileNotFoundError:
        columns = ['tutor_id', 'tutor_name', 'check_in', 'check_out', 'shift_hours', 'snapshot_in', 'snapshot_out']
        df = pd.DataFrame(columns=columns)
        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
        os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
        return df

    df['check_in'] = pd.to_datetime(df['check_in'], errors='coerce')
    df['check_out'] = pd.to_datetime(df['check_out'], errors='coerce')
    
    if 'shift_hours' not in df.columns:
        valid_times = df['check_in'].notna() & df['check_out'].notna()
        df.loc[valid_times, 'shift_hours'] = (df.loc[valid_times, 'check_out'] - df.loc[valid_times, 'check_in']).dt.total_seconds() / 3600
    else:
        df['shift_hours'] = pd.to_numeric(df['shift_hours'], errors='coerce')
        mask_recalc = df['shift_hours'].isna() & df['check_in'].notna() & df['check_out'].notna()
        df.loc[mask_recalc, 'shift_hours'] = (df.loc[mask_recalc, 'check_out'] - df.loc[mask_recalc, 'check_in']).dt.total_seconds() / 3600
        
    df['shift_hours'] = df['shift_hours'].fillna(0).round(2)

    for col in ['snapshot_in', 'snapshot_out']:
        if col not in df.columns:
            df[col] = ''

    df['snapshot_in'] = df['snapshot_in'].fillna('').astype(str).apply(
        lambda x: x if x.startswith('snapshots/') or not x or x.startswith('/') else 'snapshots/' + os.path.basename(x)
    )
    df['snapshot_out'] = df['snapshot_out'].fillna('').astype(str).apply(
        lambda x: x if x.startswith('snapshots/') or not x or x.startswith('/') else 'snapshots/' + os.path.basename(x)
    )

    df = df.dropna(subset=['check_in'])
    if df.empty:
        return df

    df['date'] = df['check_in'].dt.date
    df['month_year'] = df['check_in'].dt.to_period('M').astype(str)
    df['day_name'] = df['check_in'].dt.day_name()
    df['hour'] = df['check_in'].dt.hour
    df['check_in_time_of_day'] = df['check_in'].dt.time 
    
    return df

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/dashboard-data')
def dashboard_data():
    df = load_data()
    now = datetime.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    alerts_list = []
    summary = {
        "total_checkins": 0, "total_hours": 0, "active_tutors": 0,
        "top_tutor": "N/A", "top_day": "N/A", "top_tutor_current_month": "N/A",
        "avg_daily_hours": "—", "avg_session_duration": "—", "peak_checkin_hour": "—"
    }
    logs_for_collapsible_view = []

    if not df.empty:
        df_current_month = df[df['check_in'] >= current_month_start]

        # Top Tutor (All-Time)
        top_tutor_val = "N/A"
        if 'tutor_name' in df.columns and 'shift_hours' in df.columns:
            tutor_total_hours = df.groupby('tutor_name')['shift_hours'].sum()
            if not tutor_total_hours.empty:
                try: top_tutor_val = tutor_total_hours.idxmax()
                except ValueError: pass

        # Top Tutor (This Month)
        top_tutor_current_month_val = "N/A"
        if not df_current_month.empty and 'tutor_name' in df_current_month.columns and 'shift_hours' in df_current_month.columns:
            tutor_hours_current_month = df_current_month.groupby('tutor_name')['shift_hours'].sum()
            if not tutor_hours_current_month.empty:
                try: top_tutor_current_month_val = tutor_hours_current_month.idxmax()
                except ValueError: pass

        # Top Day
        top_day_val = "N/A"
        if 'date' in df.columns and not df['date'].empty:
            date_counts = df['date'].value_counts()
            if not date_counts.empty:
                try: top_day_val = date_counts.idxmax().strftime('%A, %b %d')
                except (AttributeError, ValueError): pass

        # Avg Daily Hours
        try:
            avg_daily_hours = round(df.groupby('date')['shift_hours'].sum().mean(), 2)
        except: avg_daily_hours = "—"

        # Avg Session Duration
        try:
            avg_session_duration = round(df['shift_hours'].mean(), 2)
        except: avg_session_duration = "—"

        # Peak Check-In Hour
        try:
            peak_hour = df['hour'].mode()
            peak_checkin_hour = f"{int(peak_hour.iloc[0]):02d}:00" if not peak_hour.empty else "—"
        except: peak_checkin_hour = "—"

        summary.update({
            "total_checkins": len(df),
            "total_hours": round(df['shift_hours'].sum(), 2),
            "active_tutors": df['tutor_id'].nunique(),
            "top_tutor": top_tutor_val,
            "top_day": top_day_val,
            "top_tutor_current_month": top_tutor_current_month_val,
            "avg_daily_hours": avg_daily_hours,
            "avg_session_duration": avg_session_duration,
            "peak_checkin_hour": peak_checkin_hour
        })
        
        # Populate logs for collapsible view
        logs_for_collapsible_view = df.sort_values('check_in', ascending=False).to_dict('records')
        # Convert datetime objects to strings for JSON serialization
        for log in logs_for_collapsible_view:
            if 'check_in' in log and pd.notna(log['check_in']):
                log['check_in'] = log['check_in'].isoformat()
            if 'check_out' in log and pd.notna(log['check_out']):
                log['check_out'] = log['check_out'].isoformat()
            if 'check_in_time_of_day' in log and log['check_in_time_of_day'] is not None:
                log['check_in_time_of_day'] = str(log['check_in_time_of_day'])
            if 'date' in log and log['date'] is not None:
                log['date'] = str(log['date'])
            # Handle NaN values and other non-serializable types
            for key, value in log.items():
                if pd.isna(value):
                    log[key] = None
                elif hasattr(value, 'isoformat'):  # datetime/date objects
                    log[key] = value.isoformat()
                elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, type(None))):
                    log[key] = str(value)
        
    return jsonify({
        "summary": summary,
        "logs_for_collapsible_view": logs_for_collapsible_view,
        "alerts": alerts_list
    })

@app.route('/charts')
def charts_page():
    return render_template('charts.html')

@app.route('/get-tutors')
def get_tutors():
    df = load_data()
    if df.empty or not all(col in df.columns for col in ['tutor_id', 'tutor_name']):
        return jsonify([])
    # Ensure tutor_id is string for consistency if it's numeric, and handle potential NaNs in name
    df_tutors = df[['tutor_id', 'tutor_name']].copy()
    df_tutors['tutor_id'] = df_tutors['tutor_id'].astype(str)
    df_tutors['tutor_name'] = df_tutors['tutor_name'].fillna(f"Tutor (ID: {df_tutors['tutor_id']})") # Fallback for NaN names

    tutors = df_tutors.drop_duplicates().sort_values(by='tutor_name').to_dict(orient='records')
    return jsonify(tutors)

def apply_filters(df_to_filter, filters):
    print(f"APPLY_FILTERS - Incoming filters: {filters}")  # Enable debug logging
    if df_to_filter.empty:
        print("APPLY_FILTERS - DataFrame is empty at start.")  # Enable debug logging
        return df_to_filter 
    df = df_to_filter.copy()
    print(f"APPLY_FILTERS - Starting DataFrame shape: {df.shape}")  # Enable debug logging
    
    # Standardize parameter handling
    tutor_ids_str = filters.get('tutor_ids', filters.get('tutor_id', ''))
    if tutor_ids_str and 'tutor_id' in df.columns:
        # Ensure tutor_ids_str is treated as a string before splitting
        tutor_ids_list = [tid.strip() for tid in str(tutor_ids_str).split(',') if tid.strip()]
        if tutor_ids_list: 
            df = df[df['tutor_id'].astype(str).isin(tutor_ids_list)]
            # print(f"APPLY_FILTERS - After tutor_ids: {df.shape}")

    start_date_str = filters.get('start_date')
    if start_date_str and 'check_in' in df.columns:
        try: 
            df = df[df['check_in'] >= pd.to_datetime(start_date_str)]
            # print(f"APPLY_FILTERS - After start_date: {df.shape}")
        except Exception as e: print(f"Error applying start_date filter: {e}")
    
    end_date_str = filters.get('end_date')
    if end_date_str and 'check_in' in df.columns:
        try: 
            df = df[df['check_in'] < (pd.to_datetime(end_date_str) + pd.Timedelta(days=1))]
            # print(f"APPLY_FILTERS - After end_date: {df.shape}")
        except Exception as e: print(f"Error applying end_date filter: {e}")

    duration_filter = filters.get('duration')
    if duration_filter and 'shift_hours' in df.columns:
        if duration_filter == "<1": df = df[df['shift_hours'] < 1]
        elif duration_filter == "1-2": df = df[(df['shift_hours'] >= 1) & (df['shift_hours'] <= 2)]
        elif duration_filter == "2-4": df = df[(df['shift_hours'] >= 2) & (df['shift_hours'] <= 4)]
        elif duration_filter == "4+": df = df[df['shift_hours'] > 4]
        # print(f"APPLY_FILTERS - After duration: {df.shape}")
    
    day_type = filters.get('day_type')
    if day_type and 'check_in' in df.columns:
        if day_type.lower() == "weekday": 
            df = df[df['check_in'].dt.weekday < 5]
        elif day_type.lower() == "weekend": 
            df = df[df['check_in'].dt.weekday >= 5]
        elif day_type.lower() == "monday": 
            df = df[df['check_in'].dt.weekday == 0]
        elif day_type.lower() == "tuesday": 
            df = df[df['check_in'].dt.weekday == 1]
        elif day_type.lower() == "wednesday": 
            df = df[df['check_in'].dt.weekday == 2]
        elif day_type.lower() == "thursday": 
            df = df[df['check_in'].dt.weekday == 3]
        elif day_type.lower() == "friday": 
            df = df[df['check_in'].dt.weekday == 4]
        elif day_type.lower() == "saturday": 
            df = df[df['check_in'].dt.weekday == 5]
        elif day_type.lower() == "sunday": 
            df = df[df['check_in'].dt.weekday == 6]
        # print(f"APPLY_FILTERS - After day_type: {df.shape}")

    shift_start_hour = filters.get('shift_start_hour')
    shift_end_hour = filters.get('shift_end_hour')
    if shift_start_hour is not None and shift_end_hour is not None and 'check_in_time_of_day' in df.columns:
        try:
            # Handle both string and numeric inputs
            start_hour = int(shift_start_hour)
            end_hour = int(shift_end_hour)
            start_time = datetime.strptime(f"{start_hour:02d}", "%H").time()
            end_time = datetime.strptime(f"{end_hour:02d}", "%H").time()
            
            df = df[(df['check_in_time_of_day'] >= start_time) & (df['check_in_time_of_day'] <= end_time)]
        except (ValueError, TypeError) as e:
            print(f"Error applying shift_time filter: {e}")
    
    # Advanced Filters
    min_hours = filters.get('minHours')
    if min_hours and 'shift_hours' in df.columns:
        try:
            min_hours_val = float(min_hours)
            df = df[df['shift_hours'] >= min_hours_val]
        except (ValueError, TypeError) as e:
            print(f"Error applying minHours filter: {e}")
    
    max_hours = filters.get('maxHours')
    if max_hours and 'shift_hours' in df.columns:
        try:
            max_hours_val = float(max_hours)
            df = df[df['shift_hours'] <= max_hours_val]
        except (ValueError, TypeError) as e:
            print(f"Error applying maxHours filter: {e}")
    
    min_sessions = filters.get('minSessions')
    if min_sessions and 'tutor_id' in df.columns:
        try:
            min_sessions_val = int(min_sessions)
            session_counts = df['tutor_id'].value_counts()
            valid_tutors = session_counts[session_counts >= min_sessions_val].index
            df = df[df['tutor_id'].isin(valid_tutors)]
        except (ValueError, TypeError) as e:
            print(f"Error applying minSessions filter: {e}")
    
    max_sessions = filters.get('maxSessions')
    if max_sessions and 'tutor_id' in df.columns:
        try:
            max_sessions_val = int(max_sessions)
            session_counts = df['tutor_id'].value_counts()
            valid_tutors = session_counts[session_counts <= max_sessions_val].index
            df = df[df['tutor_id'].isin(valid_tutors)]
        except (ValueError, TypeError) as e:
            print(f"Error applying maxSessions filter: {e}")
    
    session_pattern = filters.get('sessionPattern')
    if session_pattern and 'check_in' in df.columns and 'tutor_id' in df.columns:
        if session_pattern == 'weekend_only':
            df = df[df['check_in'].dt.weekday >= 5]
        elif session_pattern == 'weekday_only':
            df = df[df['check_in'].dt.weekday < 5]
        elif session_pattern == 'high_frequency':
            # Filter for tutors with >3 sessions per week
            weekly_counts = df.groupby(['tutor_id', df['check_in'].dt.isocalendar().week]).size()
            high_freq_tutors = weekly_counts[weekly_counts > 3].index.get_level_values('tutor_id').unique()
            df = df[df['tutor_id'].isin(high_freq_tutors)]
        elif session_pattern == 'low_frequency':
            # Filter for tutors with <2 sessions per week
            weekly_counts = df.groupby(['tutor_id', df['check_in'].dt.isocalendar().week]).size()
            low_freq_tutors = weekly_counts[weekly_counts < 2].index.get_level_values('tutor_id').unique()
            df = df[df['tutor_id'].isin(low_freq_tutors)]
        elif session_pattern == 'consistent':
            # Filter for tutors with regular patterns (mock implementation)
            # In real implementation, calculate variance in check-in times
            pass
        elif session_pattern == 'irregular':
            # Filter for tutors with irregular patterns (mock implementation)
            pass
    
    time_of_day = filters.get('timeOfDay')
    if time_of_day and 'hour' in df.columns:
        if time_of_day == 'early_morning':
            df = df[(df['hour'] >= 6) & (df['hour'] < 9)]
        elif time_of_day == 'morning':
            df = df[(df['hour'] >= 9) & (df['hour'] < 12)]
        elif time_of_day == 'afternoon':
            df = df[(df['hour'] >= 12) & (df['hour'] < 17)]
        elif time_of_day == 'evening':
            df = df[(df['hour'] >= 17) & (df['hour'] < 21)]
        elif time_of_day == 'night':
            df = df[(df['hour'] >= 21) | (df['hour'] < 6)]
    
    punctuality_filter = filters.get('punctualityFilter')
    if punctuality_filter:
        # Mock punctuality filtering - in real implementation, compare with expected times
        # For now, randomly assign punctuality status based on tutor_id
        if punctuality_filter == 'early':
            df = df[df['tutor_id'].astype(str).str[-1].isin(['1', '2', '3'])]
        elif punctuality_filter == 'ontime':
            df = df[df['tutor_id'].astype(str).str[-1].isin(['4', '5', '6', '7'])]
        elif punctuality_filter == 'late':
            df = df[df['tutor_id'].astype(str).str[-1].isin(['8', '9', '0'])]
    
    exclude_weekends = filters.get('excludeWeekends')
    if exclude_weekends and 'check_in' in df.columns:
        # Handle both string 'true' and boolean True
        if exclude_weekends == 'true' or exclude_weekends is True:
            df = df[df['check_in'].dt.weekday < 5]
    
    exclude_holidays = filters.get('excludeHolidays')
    if exclude_holidays and 'check_in' in df.columns:
        # Handle both string 'true' and boolean True
        if exclude_holidays == 'true' or exclude_holidays is True:
            # Mock holiday exclusion - in real implementation, use a holiday calendar
            # For now, exclude some common holiday dates (example: New Year's Day, Christmas)
            holiday_dates = ['2024-01-01', '2024-12-25', '2023-01-01', '2023-12-25']
            df = df[~df['check_in'].dt.date.astype(str).isin(holiday_dates)]
    
    # Additional advanced filters
    outlier_handling = filters.get('outlierHandling')
    if outlier_handling and outlier_handling != 'include' and 'shift_hours' in df.columns:
        if outlier_handling == 'exclude_extreme':
            # Remove extreme outliers (beyond 3 standard deviations)
            mean_hours = df['shift_hours'].mean()
            std_hours = df['shift_hours'].std()
            df = df[abs(df['shift_hours'] - mean_hours) <= 3 * std_hours]
        elif outlier_handling == 'cap_outliers':
            # Cap outliers at 95th percentile
            upper_limit = df['shift_hours'].quantile(0.95)
            lower_limit = df['shift_hours'].quantile(0.05)
            df = df[(df['shift_hours'] >= lower_limit) & (df['shift_hours'] <= upper_limit)]
    
    print(f"APPLY_FILTERS - DataFrame shape at end: {df.shape}")  # Enable debug logging
    return df

@app.route('/chart-data', methods=['POST'])
def chart_data_endpoint():
    df_orig = load_data()
    filters = request.json if request.is_json else {}
    print(f"CHART_DATA - Received filters: {filters}")  # Enable debug logging
    
    df_filtered = apply_filters(df_orig, filters)
    print(f"CHART_DATA - df_filtered shape after apply_filters: {df_filtered.shape}")  # Enable debug logging 


    empty_chart_data_response = {key: {} for key in [
        'checkins_per_tutor', 'hours_per_tutor', 'daily_checkins', 'daily_hours',
        'cumulative_hours', 'cumulative_checkins', 'hourly_checkins_dist', 'monthly_hours',
        'avg_hours_per_day_of_week', 'checkins_per_day_of_week', 'hourly_activity_by_day',
        'forecast_daily_checkins']}
    empty_chart_data_response['raw_records_for_chart_context'] = []
    empty_chart_data_response['is_comparison_mode'] = False

    if df_filtered.empty:
        # print("CHART_DATA - df_filtered is empty, returning empty response.")
        return jsonify(empty_chart_data_response)

    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hours_order = [f"{h:02d}:00" for h in range(24)]
    
    tutor_ids_str = filters.get('tutor_ids', '')
    selected_tutor_ids = [tid.strip() for tid in str(tutor_ids_str).split(',') if tid.strip()] # Ensure str
    is_comparison_mode = len(selected_tutor_ids) > 1 
    # print(f"CHART_DATA - is_comparison_mode: {is_comparison_mode}, selected_tutor_ids: {selected_tutor_ids}")

    checkins_per_tutor = df_filtered['tutor_name'].value_counts().to_dict() if 'tutor_name' in df_filtered.columns else {}
    hours_per_tutor = df_filtered.groupby('tutor_name')['shift_hours'].sum().round(2).to_dict() if 'tutor_name' in df_filtered.columns and 'shift_hours' in df_filtered.columns else {}
    daily_checkins, daily_hours, cumulative_checkins, cumulative_hours, hourly_checkins_dist, monthly_hours = {}, {}, {}, {}, {}, {}
    avg_hours_per_day_of_week, checkins_per_day_of_week = {day: 0 for day in days_order}, {day: 0 for day in days_order}
    hourly_activity_by_day = {day: {hr: 0 for hr in hours_order} for day in days_order}

    if 'check_in' in df_filtered.columns:
        daily_checkins_series = df_filtered.groupby(df_filtered['check_in'].dt.date).size().sort_index()
        daily_checkins = {date_obj.strftime('%Y-%m-%d'): count for date_obj, count in daily_checkins_series.items()}
        cumulative_checkins_series = df_filtered.sort_values('check_in').set_index('check_in').groupby(pd.Grouper(freq='D')).size().cumsum()
        cumulative_checkins = {date_obj.strftime('%Y-%m-%d'): int(val) for date_obj, val in cumulative_checkins_series.items() if val > 0}
    if 'check_in' in df_filtered.columns and 'shift_hours' in df_filtered.columns:
        daily_hours_series = df_filtered.groupby(df_filtered['check_in'].dt.date)['shift_hours'].sum().round(2).sort_index()
        daily_hours = {date_obj.strftime('%Y-%m-%d'): val for date_obj, val in daily_hours_series.items()}
        cumulative_hours_series = df_filtered.sort_values('check_in').set_index('check_in').groupby(pd.Grouper(freq='D'))['shift_hours'].sum().cumsum().round(2)
        cumulative_hours = {date_obj.strftime('%Y-%m-%d'): val for date_obj, val in cumulative_hours_series.items() if val > 0}
    if 'hour' in df_filtered.columns:
        hourly_series = df_filtered.groupby('hour').size().sort_index()
        hourly_checkins_dist = {f"{int(h):02d}:00": count for h, count in hourly_series.items()}
    if 'month_year' in df_filtered.columns and 'shift_hours' in df_filtered.columns:
        monthly_hours_series = df_filtered.groupby('month_year')['shift_hours'].sum().round(2).sort_index()
        monthly_hours = {str(month_obj): val for month_obj, val in monthly_hours_series.items()}
    if 'day_name' in df_filtered.columns and 'shift_hours' in df_filtered.columns:
        avg_series = df_filtered.groupby('day_name')['shift_hours'].mean().round(2).reindex(days_order).fillna(0)
        avg_hours_per_day_of_week = {day: val for day, val in avg_series.items()}
    if 'day_name' in df_filtered.columns:
        checkins_series = df_filtered['day_name'].value_counts().reindex(days_order).fillna(0)
        checkins_per_day_of_week = {day: int(val) for day, val in checkins_series.items()}
    if 'day_name' in df_filtered.columns and 'hour' in df_filtered.columns:
        pivot_table = pd.pivot_table(df_filtered, index='day_name', columns='hour', aggfunc='size', fill_value=0)
        for day_name_idx, row in pivot_table.reindex(days_order, fill_value=0).iterrows():
            day_name = str(day_name_idx) 
            if day_name in hourly_activity_by_day:
                for hour_int, count in row.items():
                    hour_str = f"{int(hour_int):02d}:00"
                    if hour_str in hourly_activity_by_day[day_name]: hourly_activity_by_day[day_name][hour_str] = count
    
    daily_hours_comparison, daily_checkins_comparison = {}, {}
    if is_comparison_mode and 'tutor_id' in df_filtered.columns and 'tutor_name' in df_filtered.columns:
        for tutor_id_comp in selected_tutor_ids:
            df_tutor = df_filtered[df_filtered['tutor_id'].astype(str) == tutor_id_comp]
            if df_tutor.empty: continue
            tutor_name = df_tutor['tutor_name'].iloc[0]
            if 'check_in' in df_tutor.columns and 'shift_hours' in df_tutor.columns:
                t_daily_hours_series = df_tutor.groupby(df_tutor['check_in'].dt.date)['shift_hours'].sum().round(2).sort_index()
                daily_hours_comparison[tutor_name] = {date_obj.strftime('%Y-%m-%d'): val for date_obj, val in t_daily_hours_series.items()}
            if 'check_in' in df_tutor.columns:
                t_daily_checkins_series = df_tutor.groupby(df_tutor['check_in'].dt.date).size().sort_index()
                daily_checkins_comparison[tutor_name] = {date_obj.strftime('%Y-%m-%d'): count for date_obj, count in t_daily_checkins_series.items()}
    
    raw_records_for_chart_context = []
    if not df_filtered.empty and all(col in df_filtered.columns for col in ['tutor_id', 'tutor_name', 'check_in', 'check_out', 'shift_hours', 'snapshot_in', 'snapshot_out']):
        raw_df_copy = df_filtered.copy()
        if 'check_in' in raw_df_copy.columns: raw_df_copy['check_in_str'] = raw_df_copy['check_in'].dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'check_out' in raw_df_copy.columns: raw_df_copy['check_out_str'] = raw_df_copy['check_out'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else '—')
        if 'shift_hours' in raw_df_copy.columns: raw_df_copy['duration_str'] = raw_df_copy['shift_hours'].apply(lambda x: f"{x:.2f}" if pd.notna(x) and x > 0 else '—')
        cols_for_raw_context = ['tutor_id', 'tutor_name', 'check_in_str', 'check_out_str', 'duration_str', 'snapshot_in', 'snapshot_out']
        existing_cols_for_raw = [col for col in cols_for_raw_context if col in raw_df_copy.columns]
        if existing_cols_for_raw:
            raw_records_for_chart_context = raw_df_copy[existing_cols_for_raw].rename(columns={
                'check_in_str': 'check_in', 'check_out_str': 'check_out', 'duration_str': 'shift_hours'
            }).to_dict(orient='records')

    chart_key_requested = filters.get('chartKey', '')
    final_daily_checkins = daily_checkins_comparison if is_comparison_mode and chart_key_requested == 'daily_checkins' and daily_checkins_comparison else daily_checkins
    final_daily_hours = daily_hours_comparison if is_comparison_mode and chart_key_requested == 'daily_hours' and daily_hours_comparison else daily_hours

    response_data = {
        'checkins_per_tutor': checkins_per_tutor, 'hours_per_tutor': hours_per_tutor,
        'daily_checkins': final_daily_checkins, 'daily_hours': final_daily_hours,
        'cumulative_checkins': cumulative_checkins, 'cumulative_hours': cumulative_hours,
        'hourly_checkins_dist': hourly_checkins_dist, 'monthly_hours': monthly_hours,
        'avg_hours_per_day_of_week': avg_hours_per_day_of_week, 'checkins_per_day_of_week': checkins_per_day_of_week,
        'hourly_activity_by_day': hourly_activity_by_day, 'forecast_daily_checkins': {},
        'raw_records_for_chart_context': raw_records_for_chart_context,
        'is_comparison_mode': is_comparison_mode,
    }
    return jsonify(response_data)


@app.route('/check-in', methods=['POST'])
def check_in():
    data = request.form
    tutor_id = data.get('tutor_id')
    tutor_name = data.get('tutor_name', f"Tutor {tutor_id}" if tutor_id else "Unknown Tutor")
    check_in_str = data.get('check_in')
    check_out_str = data.get('check_out')
    shift_hours_str = data.get('shift_hours')

    if not tutor_id or not check_in_str:
        return "Error: Tutor ID and Check-In time are required.", 400

    shift_hours_val = None # Initialize
    if shift_hours_str:
        try:
            shift_hours_val = float(shift_hours_str)
        except ValueError:
            shift_hours_val = None # Explicitly set to None if conversion fails

    # Only try to calculate if shift_hours_val is still None AND we have check_in and check_out times
    if shift_hours_val is None and check_in_str and check_out_str:
        try:
            ci = datetime.strptime(check_in_str, '%Y-%m-%dT%H:%M')
            co = datetime.strptime(check_out_str, '%Y-%m-%dT%H:%M')
            if co > ci: # This is the line your error was related to
                shift_hours_val = round(((co - ci).total_seconds()) / 3600, 2)
        except ValueError:
            # This 'pass' means if date parsing fails or co/ci are not comparable,
            # shift_hours_val will remain as it was (None or the value from shift_hours_str if it was valid)
            pass 

    new_entry = {
        "tutor_id": tutor_id, 
        "tutor_name": tutor_name,
        "check_in": check_in_str.replace('T', ' ') + ':00' if check_in_str else None,
        "check_out": check_out_str.replace('T', ' ') + ':00' if check_out_str else None,
        "shift_hours": shift_hours_val if shift_hours_val is not None else '', # Store empty string if None
        "snapshot_in": data.get('snapshot_in', ''), 
        "snapshot_out": data.get('snapshot_out', '') 
    }
    
    df_log = None # Initialize df_log
    try: 
        df_log = pd.read_csv(CSV_FILE)
    except FileNotFoundError: 
        # If file not found, create an empty DataFrame with the correct columns
        df_log = pd.DataFrame(columns=new_entry.keys()) 
        
    # Append the new entry
    df_log = pd.concat([df_log, pd.DataFrame([new_entry])], ignore_index=True)
    
    # Save back to CSV
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True) # Ensure directory exists
    df_log.to_csv(CSV_FILE, index=False)
    
    return redirect(url_for('index'))

@app.route('/download-log')
def download_log():
    try: return send_file(CSV_FILE, as_attachment=True, download_name='tutor_check_in_log.csv')
    except FileNotFoundError: return "Log file not found.", 404

@app.route('/export-chart-filtered-data', methods=['POST'])
def export_chart_filtered_data():
    df_orig = load_data();
    if df_orig.empty: return "No data to export.", 404
    filters = request.json if request.is_json else {}
    df_filtered = apply_filters(df_orig, filters)
    if df_filtered.empty: return "No data matches filters for export.", 404
    export_cols = ['tutor_id', 'tutor_name', 'check_in', 'check_out', 'shift_hours', 'snapshot_in', 'snapshot_out']
    for col in export_cols:
        if col not in df_filtered.columns: df_filtered[col] = None
    df_export = df_filtered[export_cols].copy()
    if 'check_in' in df_export.columns: df_export['check_in'] = pd.to_datetime(df_export['check_in'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
    if 'check_out' in df_export.columns: df_export['check_out'] = pd.to_datetime(df_export['check_out'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
    df_export['check_in'] = df_export['check_in'].replace('NaT', '')
    df_export['check_out'] = df_export['check_out'].replace('NaT', '')
    output = io.BytesIO(); df_export.to_csv(output, index=False, encoding='utf-8'); output.seek(0)
    return send_file(output, as_attachment=True, download_name='chart_filtered_data.csv', mimetype='text/csv')

if __name__ == '__main__':
    if not os.path.exists(os.path.dirname(CSV_FILE)): os.makedirs(os.path.dirname(CSV_FILE))
    if not os.path.exists(SNAPSHOTS_DIR): os.makedirs(SNAPSHOTS_DIR)
    app.run(debug=True)

