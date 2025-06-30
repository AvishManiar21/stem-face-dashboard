import pandas as pd

csv_path = 'logs/face_log_with_expected.csv'
df = pd.read_csv(csv_path)

# Fill missing expected_check_in with check_in
missing = df['expected_check_in'].isna() | (df['expected_check_in'] == '')
df.loc[missing, 'expected_check_in'] = df.loc[missing, 'check_in']

df.to_csv(csv_path, index=False)
print(f"Filled {missing.sum()} missing expected_check_in values.") 