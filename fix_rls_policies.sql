-- ============================================================
-- Fix RLS Policies - Remove Infinite Recursion
-- ============================================================
-- This script fixes the Row Level Security policies that are
-- causing infinite recursion during data import
-- ============================================================

-- Drop existing problematic policies
DROP POLICY IF EXISTS "Users can view own profile" ON users;
DROP POLICY IF EXISTS "Users can view relevant appointments" ON appointments;

-- Temporarily disable RLS for import (you can re-enable later with proper policies)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE appointments DISABLE ROW LEVEL SECURITY;

-- Alternative: Create simpler policies that don't cause recursion
-- Uncomment these if you want RLS enabled (but simpler):

-- For users table - allow all authenticated users to read
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow authenticated read" ON users
--     FOR SELECT USING (auth.role() = 'authenticated');

-- For appointments - allow all authenticated users to read
-- ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow authenticated read" ON appointments
--     FOR SELECT USING (auth.role() = 'authenticated');

-- Note: For production, you should create more specific policies
-- based on your authentication setup. For now, RLS is disabled
-- to allow data import and application functionality.

SELECT 'RLS policies fixed - RLS disabled for users and appointments tables' AS status;

