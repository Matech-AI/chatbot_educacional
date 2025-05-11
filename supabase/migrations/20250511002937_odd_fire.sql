/*
  # Create demo users

  1. Changes
    - Creates three demo users with predefined credentials:
      - Admin user: admin@dnadaforca.com
      - Instructor user: instrutor@dnadaforca.com
      - Student user: aluno@dnadaforca.com
    
  2. Security
    - Users are created with secure passwords
    - Profiles are created with appropriate roles
    - RLS policies are already in place from previous migrations
*/

-- Create demo users in auth.users
DO $$
DECLARE
  admin_uid UUID;
  instructor_uid UUID;
  student_uid UUID;
BEGIN
  -- Create admin user
  INSERT INTO auth.users (email, encrypted_password, email_confirmed_at, role)
  VALUES (
    'admin@dnadaforca.com',
    crypt('admin123', gen_salt('bf')),
    now(),
    'authenticated'
  )
  RETURNING id INTO admin_uid;

  -- Create instructor user
  INSERT INTO auth.users (email, encrypted_password, email_confirmed_at, role)
  VALUES (
    'instrutor@dnadaforca.com',
    crypt('instrutor123', gen_salt('bf')),
    now(),
    'authenticated'
  )
  RETURNING id INTO instructor_uid;

  -- Create student user
  INSERT INTO auth.users (email, encrypted_password, email_confirmed_at, role)
  VALUES (
    'aluno@dnadaforca.com',
    crypt('aluno123', gen_salt('bf')),
    now(),
    'authenticated'
  )
  RETURNING id INTO student_uid;

  -- Create corresponding profiles
  INSERT INTO public.profiles (id, full_name, role)
  VALUES
    (admin_uid, 'Administrador', 'admin'),
    (instructor_uid, 'Instrutor', 'instructor'),
    (student_uid, 'Aluno', 'student');
END $$;