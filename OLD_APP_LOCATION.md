# Old App (Face Recognition System) Location

## Where is the Old App?

The old face recognition app is located in the **`app/legacy/`** directory. It's currently **DISABLED** by default and can be enabled via the feature toggle.

## Directory Structure

```
stem-face-dashboard/
├── app/
│   ├── legacy/                    ← OLD APP IS HERE
│   │   ├── routes.py             # Legacy routes (charts, calendar, check-in/out)
│   │   ├── analytics.py           # Face recognition analytics
│   │   ├── attendance.py          # Check-in/check-out logic
│   │   ├── forecasting.py        # Forecasting features
│   │   ├── ai_insights.py        # AI insights
│   │   └── templates/            # Legacy templates
│   │       ├── charts.html
│   │       ├── calendar.html
│   │       └── ...
│   │
│   └── scheduling/                ← NEW APP (WCOnline-style)
│       ├── routes.py
│       └── templates/
│
└── templates/
    ├── dashboard.html            # Old face recognition dashboard
    ├── charts.html              # Analytics charts
    └── calendar.html            # Attendance calendar
```

## Current Status

**Face Recognition is DISABLED by default:**
- Legacy routes are NOT registered
- Old app is NOT accessible
- System shows scheduling interface instead

## How to Access the Old App

### Step 1: Enable Face Recognition Feature

1. **Login as admin/authorized user:**
   - Go to: http://localhost:5000/login
   - Login with admin credentials or user in `FEATURE_TOGGLE_ALLOWED_USERS`

2. **Access Admin Dashboard:**
   - Go to: http://localhost:5000/admin/dashboard

3. **Enable Face Recognition:**
   - Find "Face Recognition" toggle
   - Switch it ON
   - Click "Save Changes"
   - **Restart the Flask app** (required for blueprint registration)

### Step 2: Access Old App Routes

Once enabled, the old app routes become available:

#### Main Routes:
- **`/`** - Main face recognition dashboard (replaces scheduling)
- **`/dashboard`** - Face recognition dashboard
- **`/legacy/charts`** - Analytics charts page
- **`/legacy/calendar`** - Attendance calendar page

#### API Routes:
- **`/legacy/chart-data`** - Chart data API
- **`/legacy/api/calendar-data`** - Calendar data API
- **`/legacy/api/calendar-day-details`** - Day details API
- **`/legacy/check-in`** - Check-in endpoint
- **`/legacy/get-tutors`** - Get tutors list
- **`/legacy/export-punctuality-csv`** - Export data
- **`/legacy/download-log`** - Download logs

## Old App Features

When enabled, the old app provides:

1. **Face Recognition Dashboard** (`/`)
   - Check-in/check-out system
   - Attendance tracking
   - Snapshot viewer

2. **Analytics Charts** (`/legacy/charts`)
   - Check-ins per tutor
   - Punctuality analysis
   - Time-based analytics
   - Forecasting

3. **Attendance Calendar** (`/legacy/calendar`)
   - Monthly view
   - Daily attendance details
   - Check-in/check-out times

4. **Check-in/Check-out System**
   - Manual check-in/out
   - Face recognition integration
   - Snapshot capture

## Data Files

The old app uses these data files:
- `data/legacy/face_log.csv` - Face recognition logs
- `data/legacy/shifts.csv` - Shift schedules
- `data/legacy/face_log_with_expected.csv` - Expected check-ins

## Switching Between Apps

### To Use Old App (Face Recognition):
1. Enable `face_recognition` feature toggle
2. Restart app
3. Visit `/` → Shows face recognition dashboard

### To Use New App (Scheduling):
1. Disable `face_recognition` feature toggle (default)
2. Restart app
3. Visit `/` → Shows scheduling dashboard

## Code Location Summary

| Component | Location | Status |
|-----------|----------|--------|
| Legacy Routes | `app/legacy/routes.py` | Disabled by default |
| Legacy Analytics | `app/legacy/analytics.py` | Available when enabled |
| Legacy Templates | `app/legacy/templates/` | Available when enabled |
| Old Dashboard | `templates/dashboard.html` | Available when enabled |
| Scheduling Routes | `app/scheduling/routes.py` | Always active |
| Feature Toggle | `app/admin/routes.py` | Always active |

## Notes

- The old app code is **NOT deleted** - it's just disabled
- All legacy code is in `app/legacy/` directory
- Feature toggle controls whether it's loaded
- When disabled, legacy routes return 404
- When enabled, legacy routes work normally
- Both apps can coexist, but only one is shown at `/`


