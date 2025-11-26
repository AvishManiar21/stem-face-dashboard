# Setup Feature Toggle Access

## Quick Setup Guide

### Step 1: Create a .env file (if you don't have one)

Create a `.env` file in the project root with:

```env
# Feature Toggle Access Control
# Add your email or user_id here to grant access to /admin/settings
FEATURE_TOGGLE_ALLOWED_USERS=your-email@example.com
```

### Step 2: Or Use Admin Role

If you have a user with `admin`, `system_admin`, or `manager` role, you can use that account directly.

### Step 3: Access the Feature Toggle Page

1. Start your Flask app: `python app.py`
2. Log in at: http://localhost:5000/login
3. Navigate to: http://localhost:5000/admin/settings

## Access Methods

### Method 1: Environment Variable (Specific Users)
```env
FEATURE_TOGGLE_ALLOWED_USERS=admin@gannon.edu,superuser@gannon.edu
```

### Method 2: Admin Role (Automatic)
Users with these roles automatically have access:
- `admin`
- `system_admin`  
- `manager`

## Example .env Configuration

```env
SECRET_KEY=your-secret-key-here
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# Feature Toggle Access - Add your email here
FEATURE_TOGGLE_ALLOWED_USERS=admin@gannon.edu
```

## Testing Access

1. **Without login**: Try accessing `/admin/settings` → Should redirect to `/login`
2. **With non-admin user**: Login as regular user → Should get 403 Forbidden
3. **With admin/allowed user**: Login as admin → Should see feature toggles

## Notes

- The feature toggle system works in both `app.py` and `app/__init__.py` (factory app)
- Access is checked on both the GET and POST endpoints
- Changes to feature flags take effect immediately
- Some features may require server restart to fully apply

