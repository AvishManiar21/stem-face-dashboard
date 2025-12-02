# Fix RLS Policies Before Importing Data

## Problem
The Row Level Security (RLS) policies are causing infinite recursion errors when trying to import data. This is because the policy checks the `users` table to determine permissions, which creates a circular dependency.

## Solution

### Step 1: Fix RLS Policies in Supabase

1. Go to your Supabase Dashboard: https://app.supabase.com
2. Select your **stem-face-dashboard** project
3. Go to **SQL Editor** → **New Query**
4. Copy and paste the contents of `fix_rls_policies.sql`
5. Click **Run**

This will:
- Remove the problematic RLS policies
- Temporarily disable RLS on `users` and `appointments` tables
- Allow data import to proceed

### Step 2: Re-run the Import

After fixing the RLS policies, run the import again:

```bash
python import_csv_to_supabase.py
```

### Step 3: (Optional) Re-enable RLS Later

Once data is imported and your application is working, you can create more specific RLS policies based on your authentication needs. For now, having RLS disabled allows the application to function properly.

## What Was Imported Successfully

From the first import attempt:
- ✅ **25 courses** - imported successfully
- ✅ **30 shifts** - imported successfully  
- ✅ **100 audit log entries** - imported successfully

## What Needs to Be Imported

After fixing RLS:
- ⏳ **26 users** - blocked by RLS policy
- ⏳ **20 tutors** - blocked (depends on users)
- ⏳ **50 appointments** - blocked by RLS policy
- ⏳ **38 shift assignments** - blocked (depends on tutors)
- ⏳ **63 availability records** - blocked (depends on tutors)
- ⏳ **75 tutor-course relationships** - blocked (depends on tutors)

## Next Steps

1. Run `fix_rls_policies.sql` in Supabase SQL Editor
2. Run `python import_csv_to_supabase.py` again
3. Verify all data is imported
4. Test your application

