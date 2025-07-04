import pandas as pd
import os
from datetime import datetime

FACE_LOG = 'logs/face_log_with_expected.csv'
AUDIT_LOG = 'logs/audit_log.csv'

# Load face log
if not os.path.exists(FACE_LOG):
    print(f"File not found: {FACE_LOG}")
    exit(1)
face_df = pd.read_csv(FACE_LOG)

# Prepare audit log entries
entries = []
for _, row in face_df.iterrows():
    tutor_id = row.get('tutor_id', '')
    tutor_name = row.get('tutor_name', '')
    user_email = ''  # If you have a mapping from tutor_id to email, fill here
    ip_address = ''
    user_agent = ''
    # Check-in
    check_in = row.get('check_in')
    if pd.notna(check_in):
        entries.append({
            'timestamp': check_in,
            'user_email': user_email,
            'action': 'TUTOR_CHECK_IN',
            'details': f'{tutor_name} ({tutor_id}) checked in',
            'ip_address': ip_address,
            'user_agent': user_agent
        })
    # Check-out
    check_out = row.get('check_out')
    if pd.notna(check_out):
        entries.append({
            'timestamp': check_out,
            'user_email': user_email,
            'action': 'TUTOR_CHECK_OUT',
            'details': f'{tutor_name} ({tutor_id}) checked out',
            'ip_address': ip_address,
            'user_agent': user_agent
        })

# Load existing audit log (if any, and not just header)
audit_cols = ['timestamp','user_email','action','details','ip_address','user_agent']
if os.path.exists(AUDIT_LOG):
    audit_df = pd.read_csv(AUDIT_LOG)
    # Remove all old TUTOR_CHECK_IN/OUT entries to avoid duplicates
    audit_df = audit_df[~audit_df['action'].isin(['TUTOR_CHECK_IN','TUTOR_CHECK_OUT'])]
else:
    audit_df = pd.DataFrame(columns=audit_cols)

# Append new entries
audit_df = pd.concat([audit_df, pd.DataFrame(entries)], ignore_index=True)
# Sort by timestamp
if 'timestamp' in audit_df.columns:
    audit_df['timestamp'] = pd.to_datetime(audit_df['timestamp'], errors='coerce')
    audit_df = audit_df.sort_values('timestamp')
# Save
os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
audit_df.to_csv(AUDIT_LOG, index=False)
print(f"Backfilled {len(entries)} audit log entries from face log.") 