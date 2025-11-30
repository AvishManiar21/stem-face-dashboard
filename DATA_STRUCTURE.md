# Data Structure and Usage Documentation

## Overview
This project uses CSV files stored in `data/core/` directory to manage a tutoring/scheduling system. The data is loaded into pandas DataFrames and processed by the `SchedulingAnalytics` class for analytics and visualization.

---

## CSV Files in `data/core/`

### 1. **appointments.csv** - Core Appointment Data
**Purpose**: Stores all tutoring appointments/sessions

**Columns**:
- `appointment_id` - Unique identifier (e.g., APT00001)
- `tutor_id` - References tutor (e.g., T2321056)
- `student_name` - Student's name
- `student_email` - Student's email
- `course_id` - References course (e.g., CRS0004)
- `appointment_date` - Date of appointment (YYYY-MM-DD)
- `start_time` - Start time (HH:MM:SS format)
- `end_time` - End time (HH:MM:SS format)
- `status` - Appointment status (scheduled, completed, cancelled)
- `notes` - Additional notes
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

**How it's used**:
- **Primary data source** for all analytics and charts
- Filtered by date range, tutor, course, status, duration, day type, and shift hours
- Duration is calculated: `duration_hours = (end_time - start_time) / 3600`
- Used for metrics like:
  - Appointments per tutor
  - Daily appointments
  - Hours per tutor
  - Appointments by status
  - Course popularity
  - Hourly distribution

---

### 2. **tutors.csv** - Tutor Information
**Purpose**: Stores tutor profile and capability data

**Columns**:
- `tutor_id` - Unique identifier (e.g., T4803771)
- `user_id` - References user account (e.g., USER0001)
- `bio` - Tutor biography/description
- `specializations` - Comma-separated list of subjects (e.g., "Mathematics,Biology")
- `max_appointments_per_day` - Maximum appointments tutor can handle
- `is_available` - Boolean availability flag
- `joined_date` - When tutor joined the system

**How it's used**:
- Merged with `users.csv` to get full names and emails
- Used to replace tutor IDs with names in charts
- Referenced when filtering appointments by tutor
- Used for tutor-specific analytics

---

### 3. **users.csv** - User Accounts
**Purpose**: Stores all user accounts (admins, tutors, students)

**Columns**:
- `user_id` - Unique identifier (e.g., USER0001, ADMIN001)
- `email` - User's email address
- `password_hash` - Hashed password
- `full_name` - User's full name
- `role` - User role (admin, tutor, student)
- `is_active` - Account active status
- `created_at` - Account creation timestamp
- `last_login` - Last login timestamp

**How it's used**:
- Merged with `tutors.csv` to enrich tutor data with names and emails
- Used for authentication and authorization
- Provides full names for display in charts instead of IDs

---

### 4. **courses.csv** - Course Catalog
**Purpose**: Stores course information

**Columns**:
- `course_id` - Unique identifier (e.g., CRS0001)
- `course_code` - Course code (e.g., COM410)
- `course_name` - Full course name (e.g., "Python Programming")
- `department` - Department name (e.g., "Computer Science")
- `description` - Course description
- `is_active` - Course active status
- `created_at` - Course creation timestamp

**How it's used**:
- Merged with appointments to show course names instead of IDs
- Used for "Course Popularity" charts
- Referenced when filtering appointments by course
- Provides course context for analytics

---

### 5. **shifts.csv** - Shift Templates
**Purpose**: Defines shift patterns (time slots and days)

**Columns**:
- `shift_id` - Unique identifier (e.g., SH0001)
- `shift_name` - Descriptive name (e.g., "Morning Shift - Monday")
- `start_time` - Shift start time (HH:MM:SS)
- `end_time` - Shift end time (HH:MM:SS)
- `days_of_week` - Comma-separated days (e.g., "Monday,Wednesday,Friday")
- `created_by` - User who created the shift
- `created_at` - Creation timestamp
- `active` - Shift active status

**How it's used**:
- Defines available time slots for scheduling
- Used for shift coverage analytics
- Referenced by shift assignments

---

### 6. **shift_assignments.csv** - Tutor Shift Assignments
**Purpose**: Links tutors to specific shifts for date ranges

**Columns**:
- `assignment_id` - Unique identifier (e.g., SA00001)
- `shift_id` - References shift (e.g., SH0029)
- `tutor_id` - References tutor (e.g., T4803771)
- `tutor_name` - Tutor's name (denormalized for convenience)
- `start_date` - Assignment start date
- `end_date` - Assignment end date
- `assigned_by` - User who made the assignment
- `assigned_at` - Assignment timestamp
- `active` - Assignment active status

**How it's used**:
- Tracks which tutors are assigned to which shifts
- Used for shift coverage and availability analytics
- Helps determine tutor availability windows

---

### 7. **availability.csv** - Tutor Availability Windows
**Purpose**: Defines when tutors are available for appointments

**Columns**:
- `availability_id` - Unique identifier (e.g., AV00001)
- `tutor_id` - References tutor (e.g., T4803771)
- `day_of_week` - Day name (Monday, Tuesday, etc.)
- `start_time` - Available start time (HH:MM:SS)
- `end_time` - Available end time (HH:MM:SS)
- `is_recurring` - Whether this is a recurring availability
- `effective_date` - When availability starts
- `end_date` - When availability ends

**How it's used**:
- Defines tutor availability patterns
- Used for scheduling and capacity planning
- Helps calculate tutor availability hours

---

### 8. **audit_log.csv** - System Activity Log
**Purpose**: Tracks all system actions for auditing

**Columns**:
- `log_id` - Unique identifier (e.g., LOG000007)
- `user_id` - User who performed the action
- `action` - Action type (create, update, delete, login, logout)
- `resource_type` - Type of resource (tutor, shift, assignment, etc.)
- `resource_id` - ID of the affected resource
- `details` - Action description
- `ip_address` - IP address of the user
- `timestamp` - When the action occurred

**How it's used**:
- Security and compliance tracking
- Audit trail for administrative actions
- User activity monitoring

---

### 9. **tutor_courses.csv** - Tutor-Course Relationships
**Purpose**: Links tutors to courses they can teach

**Columns**:
- (Structure not fully visible, but likely contains tutor_id and course_id)

**How it's used**:
- Defines which tutors are qualified for which courses
- Used for matching tutors to course requests

---

## Data Flow and Processing

### 1. **Data Loading** (`SchedulingAnalytics.__init__`)
When the analytics class is initialized:
1. All CSV files are loaded into pandas DataFrames
2. Date/time columns are parsed and converted to proper types
3. `tutors.csv` and `users.csv` are merged to enrich tutor data with names
4. Duration is calculated for appointments: `duration_hours = (end_time - start_time) / 3600`

### 2. **Data Filtering** (`filter_data` method)
Appointments are filtered based on:
- **Date Range**: `start_date` and `end_date`
- **Tutors**: `tutor_ids` (comma-separated list)
- **Courses**: `course_ids` (comma-separated list)
- **Status**: `status` (scheduled, completed, cancelled)
- **Duration**: `duration` (exact value or range like "1-2")
- **Day Type**: `day_type` (weekday/weekend)
- **Shift Hours**: `shift_start_hour` and `shift_end_hour` (0-23)

### 3. **Analytics Methods**
Each chart type has a corresponding method that:
1. Calls `filter_data()` with provided filters
2. Groups/aggregates the filtered data
3. Replaces IDs with human-readable names (tutors, courses)
4. Returns a dictionary suitable for chart rendering

**Example Flow**:
```
User selects filters → loadChartData() → Backend receives filters → 
filter_data() → appointments_per_tutor() → 
Group by tutor_id → Replace IDs with names → Return {name: count}
```

### 4. **Chart Data Generation**
The system supports 20+ chart types:
- **Appointments per Tutor**: Counts appointments grouped by tutor
- **Hours per Tutor**: Sums duration_hours grouped by tutor
- **Daily Appointments**: Counts appointments by date
- **Appointments by Status**: Groups by status (scheduled/completed/cancelled)
- **Course Popularity**: Counts appointments by course
- **Hourly Distribution**: Counts appointments by hour of day (0-23)
- And many more...

---

## Key Relationships

```
users.csv (user_id) ←→ tutors.csv (user_id)
tutors.csv (tutor_id) ←→ appointments.csv (tutor_id)
courses.csv (course_id) ←→ appointments.csv (course_id)
shifts.csv (shift_id) ←→ shift_assignments.csv (shift_id)
tutors.csv (tutor_id) ←→ shift_assignments.csv (tutor_id)
tutors.csv (tutor_id) ←→ availability.csv (tutor_id)
```

---

## Data Processing Features

### 1. **Automatic Calculations**
- **Duration**: Calculated from start_time and end_time
- **Day of Week**: Extracted from appointment_date
- **Hour**: Extracted from start_time for hourly analytics

### 2. **Data Enrichment**
- Tutor IDs → Full Names (via merge with users)
- Course IDs → Course Names (via merge with courses)
- Raw counts → Formatted percentages and statistics

### 3. **Filtering Capabilities**
- Multi-select tutors
- Date range selection
- Status filtering
- Time-based filtering (shift hours)
- Duration-based filtering
- Day type filtering (weekday/weekend)

---

## Usage in Charts

### Grid Layout (6 Metrics)
1. **Appointments per Tutor** - Bar chart showing appointment counts
2. **Scheduled Hours per Tutor** - Pie chart showing hours distribution
3. **Daily Appointments** - Line chart showing trends over time
4. **Appointments by Status** - Doughnut chart showing status breakdown
5. **Course Popularity** - Bar chart showing course demand
6. **Hourly Distribution** - Bar chart showing appointment times

### Single/Split Layouts
- User selects a specific metric from dropdown
- Data is filtered and aggregated based on selected filters
- Chart type can be changed (bar, line, pie, etc.)

---

## Data Integrity

- All relationships use foreign key-like references (tutor_id, course_id, etc.)
- Missing data is handled gracefully (returns empty DataFrames)
- Date/time parsing includes error handling
- Filtering validates input before processing

---

## Performance Considerations

- Data is loaded once when `SchedulingAnalytics` is instantiated
- Filtering operates on in-memory DataFrames (fast)
- Groupby operations are optimized by pandas
- No database queries - all operations are on CSV data

---

## Future Enhancements

Potential improvements:
- Move to a proper database (PostgreSQL, MySQL) for better performance
- Add data validation and constraints
- Implement data caching for frequently accessed metrics
- Add data export capabilities
- Real-time data updates via webhooks or polling

