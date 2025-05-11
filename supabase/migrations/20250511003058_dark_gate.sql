/*
  # Create demo users and profiles

  1. New Data
    - Creates three demo users (admin, instructor, student)
    - Creates corresponding profiles with appropriate roles
    - Sets up initial passwords and email confirmation

  2. Security
    - Users are created in auth.users table
    - Corresponding profiles are created in public.profiles table
    - All passwords are properly hashed
*/

-- Create demo users with proper UUID generation
DO $$
DECLARE
  admin_uid UUID := gen_random_uuid();
  instructor_uid UUID := gen_random_uuid();
  student_uid UUID := gen_random_uuid();
BEGIN
  -- Create admin user
  INSERT INTO auth.users (
    id,
    instance_id,
    email,
    encrypted_password,
    email_confirmed_at,
    raw_app_meta_data,
    raw_user_meta_data,
    aud,
    role
  ) VALUES (
    admin_uid,
    '00000000-0000-0000-0000-000000000000',
    'admin@dnadaforca.com',
    crypt('admin123', gen_salt('bf')),
    now(),
    '{"provider": "email", "providers": ["email"]}',
    '{"full_name": "Administrador"}',
    'authenticated',
    'authenticated'
  );

  -- Create instructor user
  INSERT INTO auth.users (
    id,
    instance_id,
    email,
    encrypted_password,
    email_confirmed_at,
    raw_app_meta_data,
    raw_user_meta_data,
    aud,
    role
  ) VALUES (
    instructor_uid,
    '00000000-0000-0000-0000-000000000000',
    'instrutor@dnadaforca.com',
    crypt('instrutor123', gen_salt('bf')),
    now(),
    '{"provider": "email", "providers": ["email"]}',
    '{"full_name": "Instrutor"}',
    'authenticated',
    'authenticated'
  );

  -- Create student user
  INSERT INTO auth.users (
    id,
    instance_id,
    email,
    encrypted_password,
    email_confirmed_at,
    raw_app_meta_data,
    raw_user_meta_data,
    aud,
    role
  ) VALUES (
    student_uid,
    '00000000-0000-0000-0000-000000000000',
    'aluno@dnadaforca.com',
    crypt('aluno123', gen_salt('bf')),
    now(),
    '{"provider": "email", "providers": ["email"]}',
    '{"full_name": "Aluno"}',
    'authenticated',
    'authenticated'
  );

  -- Create corresponding profiles
  INSERT INTO public.profiles (id, full_name, role)
  VALUES
    (admin_uid, 'Administrador', 'admin'),
    (instructor_uid, 'Instrutor', 'instructor'),
    (student_uid, 'Aluno', 'student');
END $$;