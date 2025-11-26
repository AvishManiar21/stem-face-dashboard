# Feature Toggle Access Control

The feature toggle system is now protected with authentication. Only authorized users can access the feature toggle settings page.

## Access Requirements

To access `/admin/settings`, a user must meet **ONE** of the following criteria:

1. **Admin Role**: User has `admin`, `system_admin`, or `manager` role
2. **Allowed User List**: User's email or user_id is in the `FEATURE_TOGGLE_ALLOWED_USERS` environment variable

## Configuration

### Option 1: Using Environment Variable (Recommended)

Add to your `.env` file:

```env
# Comma-separated list of user emails or user IDs allowed to access feature toggles
FEATURE_TOGGLE_ALLOWED_USERS=admin@example.com,superuser@example.com,USER123
```

**Example:**
```env
FEATURE_TOGGLE_ALLOWED_USERS=admin@gannon.edu,avish@gannon.edu
```

### Option 2: Using Admin Role

If a user has one of these roles, they automatically have access:
- `admin`
- `system_admin`
- `manager`

## How It Works

1. **User tries to access `/admin/settings`**
2. **System checks:**
   - Is user logged in? → If not, redirect to `/login`
   - Is user email/user_id in `FEATURE_TOGGLE_ALLOWED_USERS`? → If yes, grant access
   - Does user have admin role? → If yes, grant access
   - Otherwise → Return 403 Forbidden

## Setting Up a Feature Toggle Admin User

### Method 1: Create Admin User via CSV

1. Edit `data/core/users.csv`
2. Add a user with `role='admin'`
3. Or use the existing admin user

### Method 2: Use Environment Variable

1. Create a `.env` file in the project root
2. Add your email/user_id:
   ```env
   FEATURE_TOGGLE_ALLOWED_USERS=your-email@example.com
   ```
3. Restart the Flask app

### Method 3: Use Existing Admin Account

If you already have an admin account in the system, just log in with that account.

## Access URLs

- **Feature Toggle Page**: http://localhost:5000/admin/settings
- **Login Page**: http://localhost:5000/login

## Security Notes

- The feature toggle page requires authentication
- Only authorized users can modify feature flags
- All access attempts are logged (if audit logging is enabled)
- Changes take effect immediately (some may require server restart)

## Troubleshooting

### "Access denied" Error

1. Check if you're logged in
2. Verify your user has admin role OR is in `FEATURE_TOGGLE_ALLOWED_USERS`
3. Check your email/user_id matches exactly (case-insensitive)

### "Please login" Redirect

1. Go to `/login` and log in first
2. Then navigate to `/admin/settings`

### Can't Find User

1. Check `data/core/users.csv` for your user
2. Verify your email matches exactly
3. Check Supabase users table if using Supabase auth

