# Phase 1 & 2 Updates - Verification Guide

This document explains how to verify that Phase 1 and Phase 2 updates are working correctly.

## Phase 1: Data Structure Updates ✅

### What Was Updated:
1. **`appointments.csv`** - Added `booking_type` and `confirmation_status` fields
2. **`availability.csv`** - Added `slot_status` field
3. **`time_slots.csv`** - Created new file for granular time slot management

### How to Verify Phase 1:

#### 1. Check CSV Files Directly:
```bash
# Check appointments.csv for new fields
head -n 2 data/core/appointments.csv
# Should show: booking_type, confirmation_status columns

# Check availability.csv for new field
head -n 2 data/core/availability.csv
# Should show: slot_status column

# Check if time_slots.csv exists
ls data/core/time_slots.csv
```

#### 2. Check via Python:
```python
import pandas as pd

# Check appointments.csv
df = pd.read_csv('data/core/appointments.csv')
print("Appointments columns:", df.columns.tolist())
print("Has booking_type:", 'booking_type' in df.columns)
print("Has confirmation_status:", 'confirmation_status' in df.columns)

# Check availability.csv
df = pd.read_csv('data/core/availability.csv')
print("Availability columns:", df.columns.tolist())
print("Has slot_status:", 'slot_status' in df.columns)

# Check time_slots.csv
df = pd.read_csv('data/core/time_slots.csv')
print("Time slots columns:", df.columns.tolist())
```

#### 3. Check via Admin Dashboard:
1. Go to **Admin Dashboard** (`/admin/dashboard`)
2. Click **"View Appointments"**
3. You should see appointments with:
   - **Booking Type** (student_booked/admin_scheduled)
   - **Confirmation Status** (pending/confirmed/cancelled)

---

## Phase 2: Backend Development ✅

### What Was Created:
1. **`SchedulingManager`** (`app/core/scheduling_manager.py`) - Core scheduling logic
2. **CSV Watcher** (`app/core/csv_watcher.py`) - Auto-reload mechanism
3. **New API Routes** in `app/core/routes.py`:
   - `/api/schedule/week` - Get weekly schedule
   - `/api/schedule/available-slots` - Get available slots
   - `/api/appointments/book` - Book appointment
   - `/api/appointments/cancel` - Cancel appointment
   - `/api/appointments/my-appointments` - Get student appointments
   - `/api/admin/reload-data` - Manual data reload

### How to Verify Phase 2:

#### 1. Check SchedulingManager:
```python
from app.core.scheduling_manager import SchedulingManager

# Initialize manager
manager = SchedulingManager()

# Check data loaded
print(f"Loaded {len(manager.appointments)} appointments")
print(f"Loaded {len(manager.tutors)} tutors")
print(f"Loaded {len(manager.courses)} courses")

# Test methods
slots = manager.get_available_slots('T4803771', '2025-12-01')
print(f"Available slots: {len(slots)}")
```

#### 2. Check API Endpoints:
```bash
# Test weekly schedule endpoint (requires authentication)
curl -X GET "http://localhost:5000/api/schedule/week?start_date=2025-12-01"

# Test available slots endpoint
curl -X GET "http://localhost:5000/api/schedule/available-slots?tutor_id=T4803771&date=2025-12-01"
```

#### 3. Check Admin Dashboard KPIs:
1. Go to **Admin Dashboard** (`/admin/dashboard`)
2. The **4 KPI cards** should show:
   - **Total Tutors** - Real count from `tutors.csv`
   - **Active Courses** - Real count from `courses.csv`
   - **Appointments Today** - Count of today's appointments
   - **Total Users** - Count from `users.csv`

#### 4. Check Main Dashboard KPIs:
1. Go to **Main Dashboard** (`/dashboard`)
2. The **10 KPI cards** should show:
   - **Total Check-ins** - Maps to total appointments
   - **Total Hours** - Sum of appointment durations
   - **Active Tutors** - Unique tutors with appointments
   - **Avg Session Duration** - Average appointment duration
   - And 6 more secondary KPIs

---

## Verification Checklist

### Phase 1 ✅
- [x] `appointments.csv` has `booking_type` column
- [x] `appointments.csv` has `confirmation_status` column
- [x] `availability.csv` has `slot_status` column
- [x] `time_slots.csv` file exists (may be empty)

### Phase 2 ✅
- [x] `SchedulingManager` class exists and loads data
- [x] API routes are accessible (with authentication)
- [x] Admin dashboard KPIs show real data
- [x] Main dashboard KPIs show real data
- [x] Management pages work (Tutors, Courses, Appointments, Availability)

---

## Where to See Phase 1 & 2 Updates:

### 1. **Admin Dashboard** (`/admin/dashboard`)
- **KPI Cards**: Now use `SchedulingAnalytics` and `SchedulingManager`
- **Management Links**: All functional (no more "coming soon")

### 2. **Main Dashboard** (`/dashboard`)
- **KPI Cards**: Updated to use appointment data from Phase 1 & 2
- **Data Source**: Uses `appointments.csv` with new fields

### 3. **Management Pages**:
- **Tutors** (`/scheduling/tutors`) - Shows all tutors with details
- **Courses** (`/scheduling/courses`) - Shows all courses
- **Appointments** (`/scheduling/appointments`) - Shows appointments with Phase 1 fields (booking_type, confirmation_status)
- **Availability** (`/scheduling/availability`) - Shows Phase 1 & 2 info

### 4. **API Endpoints**:
- All new endpoints in `app/core/routes.py` are functional
- Use Postman or curl to test (requires authentication)

### 5. **Code Files**:
- `app/core/scheduling_manager.py` - Phase 2 core logic
- `app/core/csv_watcher.py` - Phase 2 auto-reload
- `app/core/analytics.py` - Enhanced `get_summary_stats()` for KPIs
- `app/admin/routes.py` - Updated dashboard stats endpoint
- `app/core/routes.py` - New scheduling API routes

---

## Quick Test Commands:

### Test Phase 1:
```bash
# Run enhancement script (if not already run)
python scripts/enhance_csv_files.py

# Verify columns
python -c "import pandas as pd; df = pd.read_csv('data/core/appointments.csv'); print('Columns:', df.columns.tolist())"
```

### Test Phase 2:
```bash
# Test SchedulingManager
python -c "from app.core.scheduling_manager import SchedulingManager; sm = SchedulingManager(); print(f'Loaded {len(sm.appointments)} appointments')"

# Test API (requires Flask server running)
curl http://localhost:5000/admin/api/dashboard-stats
```

---

## Troubleshooting:

### If KPIs show 0:
1. Check if CSV files exist in `data/core/`
2. Check if CSV files have data (not empty)
3. Check browser console for JavaScript errors
4. Check Flask server logs for Python errors

### If pages show "coming soon":
1. Clear browser cache
2. Restart Flask server
3. Check that templates exist in `templates/scheduling/`

### If API endpoints fail:
1. Check authentication (must be logged in)
2. Check Flask server logs
3. Verify CSV files are readable
4. Check that `SchedulingManager` initializes correctly

---

## Summary:

**Phase 1 & 2 are complete and integrated!**

- ✅ **Phase 1**: CSV files enhanced with new fields
- ✅ **Phase 2**: Backend system created with `SchedulingManager` and API routes
- ✅ **Integration**: Admin dashboard, main dashboard, and management pages all use Phase 1 & 2 data
- ✅ **KPIs**: All KPI cards now show real data from the scheduling system

You can verify everything is working by:
1. Checking the Admin Dashboard - KPIs should show real numbers
2. Clicking "Manage Tutors", "Manage Courses", "View Appointments" - Should show data, not "coming soon"
3. Checking the main Dashboard - KPIs should show appointment-based metrics

