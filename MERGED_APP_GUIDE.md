# Merged App with Feature Toggle Dashboard

## Overview

The app has been merged so that when you log in with a specific user ID, you get access to a dashboard that includes feature toggles to enable or disable system features.

## How It Works

### 1. **Single App Structure**
- Both `app.py` and the factory app (`app/__init__.py`) are now integrated
- The main entry point is `app.py`
- Feature flags work across the entire application

### 2. **Authentication & Access Control**
- Users must log in to access the admin dashboard
- Access is granted to:
  - Users with `admin`, `system_admin`, or `manager` roles
  - Users listed in `FEATURE_TOGGLE_ALLOWED_USERS` environment variable

### 3. **Admin Dashboard with Feature Toggles**
- **URL**: http://localhost:5000/admin/dashboard
- **Features**:
  - Shows all available feature flags
  - Toggle switches to enable/disable features
  - Save button to persist changes
  - Real-time status updates

## Setup Instructions

### Step 1: Configure Access

Create a `.env` file in the project root:

```env
# Add your email or user ID to grant access
FEATURE_TOGGLE_ALLOWED_USERS=your-email@example.com,another-user@example.com
```

**OR** use a user with admin role (`admin`, `system_admin`, or `manager`)

### Step 2: Start the App

```bash
python app.py
```

### Step 3: Login

1. Go to: http://localhost:5000/login
2. Login with your authorized account
3. You'll be automatically redirected to: http://localhost:5000/admin/dashboard

### Step 4: Use Feature Toggles

On the dashboard:
1. See all available features with their current status
2. Toggle features on/off using the switches
3. Click "Save Changes" to persist
4. Features update immediately (some may require server restart)

## Available Features

The system tracks these features:
- **face_recognition** - Face recognition module
- **legacy_analytics** - Legacy analytics charts
- **maintenance_mode** - Maintenance mode access

## Access Flow

```
User visits /login
    ↓
User logs in
    ↓
System checks authorization
    ↓
If authorized → Redirect to /admin/dashboard
If not authorized → Redirect to / (main dashboard)
```

## Dashboard Features

The admin dashboard includes:
- **Feature Toggles Section**: Enable/disable system features
- **Statistics Cards**: System overview
- **Quick Actions**: Links to other admin functions
- **Getting Started Guide**: Helpful instructions

## Routes

- `/login` - Login page (redirects to dashboard if already logged in and authorized)
- `/admin/dashboard` - Admin dashboard with feature toggles (requires auth)
- `/admin/settings` - Detailed settings page (requires auth)
- `/admin/settings/save` - API endpoint to save feature toggles (requires auth)

## Security

- All admin routes require authentication
- Only authorized users can access feature toggles
- Changes are saved to `data/system_config.csv`
- Access attempts are logged (if audit logging is enabled)

## Troubleshooting

### Can't Access Dashboard
1. Check if you're logged in
2. Verify your email/user_id is in `FEATURE_TOGGLE_ALLOWED_USERS` OR you have admin role
3. Check `.env` file is in the project root

### Feature Toggles Not Showing
1. Check `data/system_config.csv` exists
2. Verify feature flags are initialized
3. Check browser console for JavaScript errors

### Changes Not Saving
1. Check browser console for errors
2. Verify you have write permissions to `data/system_config.csv`
3. Check server logs for errors

## Example .env Configuration

```env
SECRET_KEY=your-secret-key-here
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# Feature Toggle Access - Add your email here
FEATURE_TOGGLE_ALLOWED_USERS=admin@gannon.edu,superuser@gannon.edu
```

## Notes

- The feature toggle system works in both `app.py` and the factory app
- Changes take effect immediately
- Some features may require server restart to fully apply
- The dashboard is accessible only to authorized users

