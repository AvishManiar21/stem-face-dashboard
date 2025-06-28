import pandas as pd

# Load the data
df = pd.read_csv('logs/face_log.csv')

print(f"Total records: {len(df)}")
print(f"Unique tutors by ID: {df['tutor_id'].nunique()}")
print(f"Unique tutors by name: {df['tutor_name'].nunique()}")

print("\nList of all tutors:")
tutor_info = df.groupby('tutor_id')['tutor_name'].first().sort_values()
for tutor_id, name in tutor_info.items():
    print(f"{tutor_id}: {name}")

print("\nTutor activity summary:")
activity = df.groupby(['tutor_id', 'tutor_name']).agg({
    'shift_hours': ['count', 'sum']
}).round(2)
activity.columns = ['sessions', 'total_hours']
activity = activity.sort_values('total_hours', ascending=False)
print(activity)