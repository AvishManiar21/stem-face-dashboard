import pandas as pd
from datetime import datetime

INPUT_FILE = 'logs/expanded_schedules.csv'
OUTPUT_FILE = 'logs/expanded_schedules.csv'

# Read the schedule
schedule = pd.read_csv(INPUT_FILE)

# Convert times to datetime for comparison
schedule['start_dt'] = pd.to_datetime(schedule['date'] + ' ' + schedule['start_time'])
schedule['end_dt'] = pd.to_datetime(schedule['date'] + ' ' + schedule['end_time'])

cleaned_rows = []
removed = []

for tutor_id, group in schedule.groupby('tutor_id'):
    for date, day_group in group.groupby('date'):
        # Sort by start time
        day_group = day_group.sort_values('start_dt')
        last_end = None
        for idx, row in day_group.iterrows():
            if last_end is None or row['start_dt'] >= last_end:
                cleaned_rows.append(row)
                last_end = row['end_dt']
            else:
                removed.append(row)

# Create cleaned DataFrame
cleaned_df = pd.DataFrame(cleaned_rows)
# Drop helper columns
cleaned_df = cleaned_df.drop(columns=['start_dt', 'end_dt'])
# Save cleaned schedule
cleaned_df.to_csv(OUTPUT_FILE, index=False)

print(f"Removed {len(removed)} overlapping sessions from the schedule.")
if removed:
    print("Sample removed rows:")
    print(pd.DataFrame(removed)[['tutor_id','tutor_name','date','start_time','end_time']].head()) 