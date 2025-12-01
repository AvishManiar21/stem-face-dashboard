-- ============================================================
-- Supabase Database Setup for STEM-FACE-DASHBOARD
-- ============================================================
-- Run this SQL in your Supabase SQL Editor to create all tables
-- Go to: Supabase Dashboard > SQL Editor > New Query
-- ============================================================

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. USERS TABLE (already exists, but ensure it has all columns)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT UNIQUE,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    salt TEXT,
    full_name TEXT,
    role TEXT DEFAULT 'tutor' CHECK (role IN ('admin', 'manager', 'lead_tutor', 'tutor', 'student')),
    tutor_id TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================
-- 2. TUTORS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS tutors (
    tutor_id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    bio TEXT,
    specializations TEXT,
    max_appointments_per_day INTEGER DEFAULT 10,
    is_available BOOLEAN DEFAULT true,
    joined_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tutors_user_id ON tutors(user_id);

-- ============================================================
-- 3. COURSES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    course_code TEXT,
    course_name TEXT NOT NULL,
    department TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(course_code);
CREATE INDEX IF NOT EXISTS idx_courses_active ON courses(is_active);

-- ============================================================
-- 4. APPOINTMENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id TEXT PRIMARY KEY,
    tutor_id TEXT REFERENCES tutors(tutor_id) ON DELETE SET NULL,
    student_name TEXT,
    student_email TEXT,
    course_id TEXT REFERENCES courses(course_id) ON DELETE SET NULL,
    appointment_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'pending')),
    booking_type TEXT DEFAULT 'student_booked' CHECK (booking_type IN ('student_booked', 'admin_scheduled')),
    confirmation_status TEXT DEFAULT 'pending' CHECK (confirmation_status IN ('pending', 'confirmed', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_appointments_tutor_id ON appointments(tutor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_student_email ON appointments(student_email);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_course_id ON appointments(course_id);

-- ============================================================
-- 5. SHIFTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS shifts (
    shift_id TEXT PRIMARY KEY,
    shift_name TEXT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    days_of_week TEXT, -- Comma-separated: "Monday,Wednesday,Friday"
    created_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_shifts_active ON shifts(active);

-- ============================================================
-- 6. SHIFT ASSIGNMENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS shift_assignments (
    assignment_id TEXT PRIMARY KEY,
    shift_id TEXT REFERENCES shifts(shift_id) ON DELETE CASCADE,
    tutor_id TEXT REFERENCES tutors(tutor_id) ON DELETE CASCADE,
    tutor_name TEXT, -- Denormalized for convenience
    start_date DATE NOT NULL,
    end_date DATE,
    assigned_by TEXT,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_shift_assignments_tutor_id ON shift_assignments(tutor_id);
CREATE INDEX IF NOT EXISTS idx_shift_assignments_shift_id ON shift_assignments(shift_id);
CREATE INDEX IF NOT EXISTS idx_shift_assignments_dates ON shift_assignments(start_date, end_date);

-- ============================================================
-- 7. AVAILABILITY TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS availability (
    availability_id TEXT PRIMARY KEY,
    tutor_id TEXT REFERENCES tutors(tutor_id) ON DELETE CASCADE,
    day_of_week TEXT NOT NULL CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_recurring BOOLEAN DEFAULT true,
    effective_date DATE NOT NULL,
    end_date DATE,
    slot_status TEXT DEFAULT 'available' CHECK (slot_status IN ('available', 'unavailable')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_availability_tutor_id ON availability(tutor_id);
CREATE INDEX IF NOT EXISTS idx_availability_day ON availability(day_of_week);
CREATE INDEX IF NOT EXISTS idx_availability_dates ON availability(effective_date, end_date);

-- ============================================================
-- 8. TIME SLOTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS time_slots (
    slot_id TEXT PRIMARY KEY,
    tutor_id TEXT REFERENCES tutors(tutor_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status TEXT DEFAULT 'available' CHECK (status IN ('available', 'booked', 'unavailable', 'pending')),
    appointment_id TEXT REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_time_slots_tutor_date ON time_slots(tutor_id, date);
CREATE INDEX IF NOT EXISTS idx_time_slots_status ON time_slots(status);

-- ============================================================
-- 9. TUTOR COURSES TABLE (Many-to-Many Relationship)
-- ============================================================
CREATE TABLE IF NOT EXISTS tutor_courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tutor_id TEXT REFERENCES tutors(tutor_id) ON DELETE CASCADE,
    course_id TEXT REFERENCES courses(course_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tutor_id, course_id)
);

CREATE INDEX IF NOT EXISTS idx_tutor_courses_tutor_id ON tutor_courses(tutor_id);
CREATE INDEX IF NOT EXISTS idx_tutor_courses_course_id ON tutor_courses(course_id);

-- ============================================================
-- 10. AUDIT LOG TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    log_id TEXT PRIMARY KEY,
    user_id TEXT,
    user_email TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

-- ============================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================
-- Enable RLS on tables (optional, but recommended for security)

-- Users table - users can read their own data, admins can read all
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text OR 
                     (SELECT role FROM users WHERE id = auth.uid()::uuid) = 'admin');

-- Appointments - tutors can see their own, students can see theirs, admins see all
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view relevant appointments" ON appointments
    FOR SELECT USING (
        tutor_id IN (SELECT tutor_id FROM tutors WHERE user_id IN (
            SELECT user_id FROM users WHERE id = auth.uid()::uuid
        ))
        OR student_email IN (SELECT email FROM users WHERE id = auth.uid()::uuid)
        OR (SELECT role FROM users WHERE id = auth.uid()::uuid) IN ('admin', 'manager')
    );

-- ============================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tutors_updated_at BEFORE UPDATE ON tutors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_availability_updated_at BEFORE UPDATE ON availability
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_time_slots_updated_at BEFORE UPDATE ON time_slots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- COMPLETION MESSAGE
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Database setup complete!';
    RAISE NOTICE 'All tables, indexes, and triggers have been created.';
    RAISE NOTICE '============================================================';
END $$;

