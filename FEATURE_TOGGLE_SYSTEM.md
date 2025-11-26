# Feature Toggle System - Face Recognition vs Scheduling

## Overview

The system now has two modes:
1. **Face Recognition Mode** (Legacy) - When `face_recognition` feature is enabled
2. **Scheduling Mode** (WCOnline-style) - Default mode when face recognition is disabled

## How It Works

### Feature Toggle Control

- **Access**: Only authorized users (admin/system_admin/manager or users in `FEATURE_TOGGLE_ALLOWED_USERS`) can access `/admin/dashboard`
- **Toggle Location**: Admin Dashboard → Feature Toggles section
- **Feature Name**: `face_recognition`

### When Face Recognition is ENABLED:
- Legacy face recognition routes are active (`/legacy/*`)
- Check-in/check-out system available
- Face recognition dashboard at `/`
- Analytics and charts available
- All face recognition features accessible

### When Face Recognition is DISABLED (Default):
- Legacy routes are disabled
- WCOnline-style scheduling system is active
- Main dashboard redirects to `/scheduling/`
- Scheduling features available:
  - Appointments management
  - Tutors management
  - Courses management
  - Availability management

## Module Structure

```
app/
├── legacy/              # Face Recognition Module (toggled)
│   ├── routes.py       # Legacy blueprint
│   ├── analytics.py    # Face recognition analytics
│   ├── attendance.py   # Check-in/check-out
│   └── templates/      # Legacy templates
│
├── scheduling/         # WCOnline-style System (always active)
│   ├── routes.py      # Scheduling blueprint
│   └── templates/     # Scheduling templates
│
└── admin/             # Feature Toggle Control
    └── routes.py      # Admin dashboard with toggles
```

## Routes

### Always Available:
- `/login` - Login page
- `/admin/dashboard` - Admin dashboard (authorized users only)
- `/admin/settings` - Detailed settings (authorized users only)
- `/scheduling/*` - Scheduling system routes

### Conditionally Available (when face_recognition enabled):
- `/legacy/*` - Face recognition routes
- `/charts` - Analytics charts
- `/calendar` - Attendance calendar
- `/dashboard` - Face recognition dashboard

## Configuration

### Enable Face Recognition:
1. Login as admin/authorized user
2. Go to `/admin/dashboard`
3. Toggle `face_recognition` to ON
4. Click "Save Changes"
5. Restart the app (some features require restart)

### Disable Face Recognition (Default):
1. Login as admin/authorized user
2. Go to `/admin/dashboard`
3. Toggle `face_recognition` to OFF
4. Click "Save Changes"
5. System switches to scheduling mode

## Access Control

### Feature Toggle Access:
- Users with roles: `admin`, `system_admin`, `manager`
- Users in `FEATURE_TOGGLE_ALLOWED_USERS` environment variable

### Example .env:
```env
FEATURE_TOGGLE_ALLOWED_USERS=admin@gannon.edu,maintenance@gannon.edu
```

## User Experience

### Regular Users:
- **Face Recognition OFF**: See scheduling system at `/`
- **Face Recognition ON**: See face recognition dashboard at `/`

### Admin/Authorized Users:
- Can access `/admin/dashboard` to toggle features
- Can see both systems when face recognition is enabled
- Can switch between modes using feature toggle

## Data Storage

- **Feature Flags**: `data/system_config.csv`
- **Scheduling Data**: `data/core/*.csv`
  - `appointments.csv`
  - `tutors.csv`
  - `courses.csv`
  - `availability.csv`
- **Legacy Data**: `data/legacy/*.csv`
  - `face_log.csv`
  - `shifts.csv`

## Migration Notes

- Face recognition code is isolated in `app/legacy/`
- Scheduling code is in `app/scheduling/`
- Both can coexist but only one is active at a time
- Feature toggle controls which system is shown to users

## Testing

1. **Test with Face Recognition OFF**:
   - Visit `/` → Should redirect to `/scheduling/`
   - Legacy routes should return 404
   - Scheduling routes should work

2. **Test with Face Recognition ON**:
   - Toggle feature on in admin dashboard
   - Restart app
   - Visit `/` → Should show face recognition dashboard
   - Legacy routes should work
   - Scheduling routes still available at `/scheduling/`

3. **Test Feature Toggle Access**:
   - Login as regular user → Should not see admin dashboard
   - Login as admin → Should see admin dashboard with toggles

