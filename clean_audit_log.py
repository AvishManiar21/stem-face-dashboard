import pandas as pd

# Read the audit log file
audit_file = 'logs/audit_log.csv'
df = pd.read_csv(audit_file)

# Remove rows where timestamp is empty (NaN or empty string)
df_clean = df.dropna(subset=['timestamp'])
df_clean = df_clean[df_clean['timestamp'] != '']

# Save the cleaned file
df_clean.to_csv(audit_file, index=False)

print(f"Cleaned audit log file. Removed {len(df) - len(df_clean)} malformed rows.")
print(f"Remaining rows: {len(df_clean)}") 