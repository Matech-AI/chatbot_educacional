/*
  # User Management System

  1. New Functions
    - `get_user_role` - Get the role of the current user
    - `is_admin` - Check if the current user is an admin
    - `manage_user_profile` - Update user profile information
    
  2. Security
    - Add admin-specific policies for user management
    - Ensure proper access control for user operations
*/

-- Function to get user role
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS text
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT role FROM profiles WHERE id = auth.uid();
$$;

-- Function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM profiles
    WHERE id = auth.uid()
    AND role = 'admin'
  );
$$;

-- Function to manage user profile
CREATE OR REPLACE FUNCTION manage_user_profile(
  target_user_id uuid,
  new_full_name text DEFAULT NULL,
  new_role text DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  -- Check if the executing user is an admin
  IF NOT is_admin() THEN
    RAISE EXCEPTION 'Only administrators can manage user profiles';
  END IF;

  -- Validate role if provided
  IF new_role IS NOT NULL AND new_role NOT IN ('admin', 'instructor', 'student') THEN
    RAISE EXCEPTION 'Invalid role specified';
  END IF;

  -- Update profile
  UPDATE profiles
  SET 
    full_name = COALESCE(new_full_name, full_name),
    role = COALESCE(new_role, role),
    updated_at = now()
  WHERE id = target_user_id;
END;
$$;

-- Admin policies for profile management
CREATE POLICY "Admins can view all profiles"
  ON profiles FOR SELECT
  TO authenticated
  USING (
    is_admin() OR id = auth.uid()
  );

CREATE POLICY "Admins can update all profiles"
  ON profiles FOR UPDATE
  TO authenticated
  USING (is_admin());

COMMENT ON FUNCTION get_user_role IS 'Get the role of the currently authenticated user';
COMMENT ON FUNCTION is_admin IS 'Check if the currently authenticated user is an admin';
COMMENT ON FUNCTION manage_user_profile IS 'Allow admins to update user profile information';