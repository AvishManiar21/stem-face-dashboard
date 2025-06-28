import pandas as pd
from datetime import datetime
import os

# Paths
SCHEDULE_FILE = 'logs/expanded_schedules.csv'
OUTPUT_FILE = 'logs/face_log.csv'
SNAPSHOT_DIR = 'snapshots'

# Read the schedule
schedule = pd.read_csv(SCHEDULE_FILE)

# Only keep rows with date up to today
schedule['date'] = pd.to_datetime(schedule['date'])
today = datetime.now().date()
schedule = schedule[schedule['date'].dt.date <= today]

# If face_log.csv exists, load it to avoid duplicates and remove future check-ins
if os.path.exists(OUTPUT_FILE):
    face_log = pd.read_csv(OUTPUT_FILE)
    face_log['check_in'] = pd.to_datetime(face_log['check_in'])
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

    check_in = datetime.strptime(check_in_str, '%Y-%m-%d %H:%M:%S')
    check_out = datetime.strptime(check_out_str, '%Y-%m-%d %H:%M:%S')
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