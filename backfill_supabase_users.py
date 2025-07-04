import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Remove specific users from Supabase Auth (corrected logic)
emails_to_remove = ["avishmaniar24@gmail.com", "maniar001@gannon.edu"]
all_users = supabase.auth.admin.list_users()
if hasattr(all_users, 'users'):
    for email in emails_to_remove:
        found = False
        for u in all_users.users:
            if u.email == email:
                supabase.auth.admin.delete_user(u.id)
                print(f"Deleted user from Supabase Auth: {email}")
                found = True
        if not found:
            print(f"User {email} not found in Supabase Auth.")

CSV_PATH = "logs/users.csv"
df = pd.read_csv(CSV_PATH)

temp_password = "TempPass123!"  # Change this or randomize as needed

def safe_val(val):
    if pd.isna(val) or val == "":
        return None
    return val

for _, row in df.iterrows():
    if str(row['active']).lower() == "true":
        email = row['email']
        full_name = row['full_name']
        role = row['role']
        # 1. Add to Supabase Auth if not present
        try:
            existing = supabase.auth.admin.list_users()
            exists = False
            if hasattr(existing, 'users'):
                for u in existing.users:
                    if u.email == email:
                        exists = True
                        break
            if exists:
                print(f"User {email} already exists in Supabase Auth.")
            else:
                resp = supabase.auth.admin.create_user({
                    "email": email,
                    "password": temp_password,
                    "user_metadata": {
                        "role": role,
                        "full_name": full_name
                    },
                    "email_confirm": True
                })
                print(f"Created user in Supabase Auth: {email}")
        except Exception as e:
            print(f"Error creating user {email} in Supabase Auth: {e}")
        # 2. Add to Supabase users table if not present
        try:
            db_users = supabase.table("users").select("email").eq("email", email).execute()
            if db_users.data:
                print(f"User {email} already exists in Supabase users table.")
            else:
                user_data = {
                    "email": email,
                    "role": role,
                    "full_name": full_name,
                    "created_at": safe_val(row.get('created_at')),
                    "updated_at": safe_val(row.get('last_login'))
                }
                print("Inserting:", user_data)
                result = supabase.table("users").insert(user_data).execute()
                print("Insert result:", result)
                print(f"Inserted user into Supabase users table: {email}")
        except Exception as e:
            print(f"Error inserting user {email} into Supabase users table: {e}") 