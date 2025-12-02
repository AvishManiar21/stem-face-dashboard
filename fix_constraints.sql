-- ============================================================
-- Fix Database Constraints to Allow All Data Values
-- ============================================================
-- This updates the CHECK constraints to allow additional
-- role and status values found in the CSV data
-- ============================================================

-- Fix users table: Add 'staff' to allowed roles
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check 
    CHECK (role IN ('admin', 'manager', 'lead_tutor', 'tutor', 'student', 'staff'));

-- Fix appointments table: Add 'no-show' to allowed statuses
ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_status_check;
ALTER TABLE appointments ADD CONSTRAINT appointments_status_check 
    CHECK (status IN ('scheduled', 'completed', 'cancelled', 'pending', 'no-show'));

SELECT 'Constraints updated successfully' AS status;

