import pandas as pd
import os
from datetime import datetime

# Legacy data paths
CSV_FILE = 'data/legacy/face_log.csv'
SNAPSHOTS_DIR = 'static/snapshots'

def load_data():
    """Load face recognition logs from CSV"""
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
