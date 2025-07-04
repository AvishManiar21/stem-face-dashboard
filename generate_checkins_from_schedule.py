import pandas as pd
from datetime import datetime
import os

# Paths
SCHEDULE_FILE = 'logs/expanded_schedules.csv'
OUTPUT_FILE = 'logs/face_log.csv'
AUDIT_LOG_FILE = 'logs/audit_log.csv'
SNAPSHOT_DIR = 'snapshots'

# Function to add audit log entry
def add_audit_log_entry(timestamp, action, details, user_email='', ip_address='', user_agent=''):
    """Add an entry to the audit log CSV file"""
    audit_entry = {
        'timestamp': timestamp,
        'user_email': user_email,
        'action': action,
        'details': details,
        'ip_address': ip_address,
        'user_agent': user_agent
    }
    
    # Create audit log file with header if it doesn't exist
    if not os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, 'w') as f:
            f.write('timestamp,user_email,action,details,ip_address,user_agent\n')
    
    # Append the entry
    with open(AUDIT_LOG_FILE, 'a') as f:
        f.write(f'{audit_entry["timestamp"]},{audit_entry["user_email"]},{audit_entry["action"]},{audit_entry["details"]},{audit_entry["ip_address"]},{audit_entry["user_agent"]}\n')

# Read the schedule
schedule = pd.read_csv(SCHEDULE_FILE)

# Only keep rows with date up to today
schedule['date'] = pd.to_datetime(schedule['date'])
today = datetime.now().date()
schedule = schedule[schedule['date'].dt.date <= today]

# If face_log.csv exists, load it to avoid duplicates and remove future check-ins
if os.path.exists(OUTPUT_FILE):
    face_log = pd.read_csv(OUTPUT_FILE)
    face_log['check_in'] = pd.to_datetime(face_log['check_in'], format='mixed')
    # Remove future check-ins
    face_log = face_log[face_log['check_in'].dt.date <= today]
    existing = set(zip(face_log['tutor_id'], face_log['check_in'].dt.strftime('%Y-%m-%d %H:%M:%S')))
else:
    face_log = pd.DataFrame()
    existing = set()

records = []
for idx, row in schedule.iterrows():
    tutor_id = row['tutor_id']
    tutor_name = row['tutor_name']
    date = row['date'].strftime('%Y-%m-%d')
    start_time = row['start_time']
    end_time = row['end_time']

    check_in_str = f"{date} {start_time}"
    check_out_str = f"{date} {end_time}"

    # Avoid duplicates
    if (tutor_id, check_in_str) in existing:
        continue

    # Parse check_in and check_out with flexible format
    from pandas import to_datetime
    try:
    check_in = datetime.strptime(check_in_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d %H:%M')
    try:
    check_out = datetime.strptime(check_out_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d %H:%M')
    shift_hours = round((check_out - check_in).total_seconds() / 3600, 2)
    snapshot_in = f"snapshots/{tutor_id}.jpg"
    snapshot_out = f"snapshots/{tutor_id}.jpg"

    records.append({
        'tutor_id': tutor_id,
        'tutor_name': tutor_name,
        'check_in': check_in.strftime('%Y-%m-%d %H:%M:%S'),
        'check_out': check_out.strftime('%Y-%m-%d %H:%M:%S'),
        'shift_hours': shift_hours,
        'snapshot_in': snapshot_in,
        'snapshot_out': snapshot_out
    })

    # Add audit log entry for this check-in
    add_audit_log_entry(
        timestamp=check_in.strftime('%Y-%m-%d %H:%M:%S'),
        action='TUTOR_CHECK_IN',
        details=f'{tutor_name} ({tutor_id}) checked in',
        user_email='',
        ip_address='',
        user_agent='Automated Script'
    )

# Append new records to face_log.csv
if records:
    new_df = pd.DataFrame(records)
    if not face_log.empty:
        output_df = pd.concat([face_log, new_df], ignore_index=True)
    else:
        output_df = new_df
    # Ensure 'check_in' is datetime before sorting
    output_df['check_in'] = pd.to_datetime(output_df['check_in'], errors='coerce')
    output_df = output_df.sort_values('check_in')
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    output_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Added {len(records)} new check-in records.")
else:
    # Even if no new records, still save cleaned file
    if not face_log.empty:
        face_log = face_log.sort_values('check_in')
        face_log.to_csv(OUTPUT_FILE, index=False)
        print("No new check-ins to add. Future check-ins removed. All up-to-date.")
    else:
        print("No new check-ins to add. All up-to-date.") 

if __name__ == "__main__":
    # Existing script logic here (already runs on import)
    # After all processing, update face_log_with_expected.csv
    import subprocess
    try:
        subprocess.run(["python", "fill_missing_expected_checkin.py"], check=True)
        print("Updated face_log_with_expected.csv for dashboard.")
    except Exception as e:
        print(f"Failed to update face_log_with_expected.csv: {e}") 