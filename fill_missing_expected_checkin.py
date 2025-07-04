import pandas as pd
import os

face_log_path = 'logs/face_log.csv'
with_expected_path = 'logs/face_log_with_expected.csv'

# Load the main face log
if os.path.exists(face_log_path):
    df = pd.read_csv(face_log_path)
else:
    df = pd.DataFrame()

# Add expected_check_in and expected_check_out columns if missing
if 'expected_check_in' not in df.columns:
    df['expected_check_in'] = df['check_in'] if 'check_in' in df.columns else ''
else:
missing = df['expected_check_in'].isna() | (df['expected_check_in'] == '')
df.loc[missing, 'expected_check_in'] = df.loc[missing, 'check_in']

if 'expected_check_out' not in df.columns:
    df['expected_check_out'] = df['check_out'] if 'check_out' in df.columns else ''
else:
    missing = df['expected_check_out'].isna() | (df['expected_check_out'] == '')
    df.loc[missing, 'expected_check_out'] = df.loc[missing, 'check_out']

# Save the fully synced file
os.makedirs(os.path.dirname(with_expected_path), exist_ok=True)
df.to_csv(with_expected_path, index=False)
print(f"Synced {len(df)} rows and all columns to face_log_with_expected.csv.") 