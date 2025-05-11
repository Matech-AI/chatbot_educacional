/*
  # Authentication and Admin Controls Setup

  1. Enable Email Authentication
    - Configure email auth provider
    - Set up password policies
    - Disable email confirmation requirement

  2. Create Admin Functions
    - User management functions
    - Role management functions
*/

-- Enable email auth
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- Create admin management functions
CREATE OR REPLACE FUNCTION create_user(
  email TEXT,
  password TEXT,
  full_name TEXT,
  role TEXT DEFAULT 'student'
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  user_id uuid;
BEGIN
  -- Validate role
  IF role NOT IN ('admin', 'instructor', 'student') THEN
    RAISE EXCEPTION 'Invalid role';
  END IF;

  -- Create auth user
  INSERT INTO auth.users (email, encrypted_password, email_confirmed_at, raw_user_meta_data)
  VALUES (
    email,
    crypt(password, gen_salt('bf')),
    now(),
    jsonb_build_object('full_name', full_name)
  )
  RETURNING id INTO user_id;

  -- Create profile
  INSERT INTO public.profiles (id, full_name, role)
  VALUES (user_id, full_name, role);

  RETURN user_id;
END;
$$;

-- Function to update user
CREATE OR REPLACE FUNCTION update_user(
  user_id uuid,
  new_email TEXT DEFAULT NULL,
  new_password TEXT DEFAULT NULL,
  new_full_name TEXT DEFAULT NULL,
  new_role TEXT DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  -- Update auth email if provided
  IF new_email IS NOT NULL THEN
    UPDATE auth.users SET email = new_email WHERE id = user_id;
  END IF;

  -- Update password if provided
  IF new_password IS NOT NULL THEN
    UPDATE auth.users 
    SET encrypted_password = crypt(new_password, gen_salt('bf'))
    WHERE id = user_id;
  END IF;

  -- Update profile if name or role provided
  IF new_full_name IS NOT NULL OR new_role IS NOT NULL THEN
    UPDATE public.profiles
    SET 
      full_name = COALESCE(new_full_name, full_name),
      role = COALESCE(new_role, role),
      updated_at = now()
    WHERE id = user_id;
  END IF;
END;
$$;

-- Function to delete user
CREATE OR REPLACE FUNCTION delete_user(user_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  DELETE FROM auth.users WHERE id = user_id;
END;
$$;

-- Admin policies
CREATE POLICY "Admins can read all profiles"
  ON profiles FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role = 'admin'
    )
  );

CREATE POLICY "Admins can update all profiles"
  ON profiles FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role = 'admin'
    )
  );

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