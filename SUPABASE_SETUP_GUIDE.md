# Supabase Setup Guide for STEM-FACE-DASHBOARD

This guide will help you set up your new Supabase project with the correct database schema and configuration.

## Step 1: Get Your Supabase Credentials

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Select your **stem-face-dashboard** project
3. Go to **Settings** → **API**
4. Copy the following:
   - **Project URL** (e.g., `https://abcdefghijklmnop.supabase.co`)
   - **anon/public key** (long JWT token starting with `eyJ...`)

## Step 2: Configure Environment Variables

### Option A: Use the Setup Script (Recommended)

Run the interactive setup script:

```bash
python setup_supabase.py
```

The script will:
- Prompt you for your Supabase URL and key
- Generate a secure Flask secret key
- Create a `.env` file with your credentials
- Test the connection

### Option B: Manual Setup

1. Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

2. Edit `.env` and add your credentials:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key-here
SECRET_KEY=your-secret-key-here
```

## Step 3: Create Database Tables

1. In your Supabase dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy and paste the entire contents of `supabase_setup.sql`
4. Click **Run** (or press Ctrl+Enter)
5. Wait for the "Database setup complete!" message

This will create:
- ✅ `users` table (with indexes)
- ✅ `tutors` table
- ✅ `courses` table
- ✅ `appointments` table
- ✅ `shifts` table
- ✅ `shift_assignments` table
- ✅ `availability` table
- ✅ `time_slots` table
- ✅ `tutor_courses` table (many-to-many)
- ✅ `audit_log` table
- ✅ Indexes for performance
- ✅ Row Level Security policies
- ✅ Triggers for automatic `updated_at` timestamps

## Step 4: Verify Setup

Run the test script to verify everything is working:

```bash
python test_supabase.py
```

You should see:
- ✅ Environment variables are set
- ✅ Supabase client created successfully
- ✅ Database tables accessible

## Step 5: (Optional) Import Existing Data

If you have existing CSV data in `data/core/`, you can import it:

1. Go to Supabase Dashboard → **Table Editor**
2. Select each table (users, tutors, courses, etc.)
3. Click **Insert** → **Import data from CSV**
4. Upload the corresponding CSV file from `data/core/`

Or use the Python import script (if available):

```bash
python scripts/import_csv_to_supabase.py
```

## Step 6: Test the Application

Start your Flask application:

```bash
python app.py
```

Or on Windows:

```bash
run_app.bat
```

Try logging in with a user account to verify authentication is working.

## Troubleshooting

### Connection Issues

**Error: "Failed to connect to Supabase"**
- Check that your `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Make sure there are no extra spaces in your `.env` file
- Verify your Supabase project is active

### Table Not Found Errors

**Error: "relation 'users' does not exist"**
- Make sure you ran the `supabase_setup.sql` script
- Check the SQL Editor for any errors
- Verify tables exist in Supabase Dashboard → Table Editor

### Authentication Issues

**Error: "Supabase Auth failed"**
- Check that Row Level Security (RLS) policies are set correctly
- Verify your `SUPABASE_KEY` is the `anon/public` key (not the `service_role` key)
- Check Supabase Dashboard → Authentication → Settings

### Permission Errors

**Error: "User not allowed" or "Insufficient permissions"**
- RLS policies might be too restrictive
- Check your user's role in the `users` table
- Verify admin users have the correct role

## Next Steps

1. **Set up Authentication**: Configure email templates, OAuth providers, etc. in Supabase Dashboard → Authentication
2. **Configure Storage**: If you need file storage, set up Supabase Storage buckets
3. **Set up Realtime**: Enable realtime subscriptions if needed
4. **Backup**: Set up automatic backups in Supabase Dashboard → Settings → Database

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_KEY` | Your Supabase anon/public key | Yes |
| `SECRET_KEY` | Flask session secret key | Yes |
| `ENABLE_FACE_RECOGNITION` | Enable face recognition features | No |
| `ENABLE_LEGACY_ANALYTICS` | Enable legacy analytics | No |
| `MAINTENANCE_MODE` | Enable maintenance mode | No |

## Support

If you encounter issues:
1. Check the Supabase logs in Dashboard → Logs
2. Review the application logs in `logs/`
3. Run `python check_supabase_details.py` to see database status
4. Verify your `.env` file is in the project root

---

**Note**: The `.env` file is already in `.gitignore` and won't be committed to version control.

