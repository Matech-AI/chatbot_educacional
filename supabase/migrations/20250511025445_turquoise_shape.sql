/*
  # Configure storage bucket and policies for materials

  1. Storage Setup
    - Create materials bucket
    - Configure bucket settings
  
  2. Security
    - Add upload policy for admins and instructors
    - Add read policy for all authenticated users
    - Add delete policy for admins and instructors
    - Restrict file types and sizes
*/

-- Create the materials bucket using storage API
SELECT storage.create_bucket('materials', {'public': false});

-- Create upload policy for admins and instructors
SELECT storage.create_policy(
  'materials',
  'upload_materials',
  'INSERT',
  'authenticated',
  storage.foldername(name) = '',
  (
    EXISTS (
      SELECT 1 FROM auth.users
      JOIN public.profiles ON auth.users.id = profiles.id
      WHERE auth.users.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
    )
    AND (lower(storage.extension(name)) = ANY (ARRAY['pdf', 'docx', 'txt', 'mp4', 'webm', 'mov']))
    AND (octet_length(content) <= 104857600)
  )
);

-- Create read policy for authenticated users
SELECT storage.create_policy(
  'materials',
  'read_materials',
  'SELECT',
  'authenticated',
  storage.foldername(name) = '',
  true
);

-- Create delete policy for admins and instructors
SELECT storage.create_policy(
  'materials',
  'delete_materials',
  'DELETE',
  'authenticated',
  storage.foldername(name) = '',
  EXISTS (
    SELECT 1 FROM auth.users
    JOIN public.profiles ON auth.users.id = profiles.id
    WHERE auth.users.id = auth.uid()
    AND profiles.role IN ('admin', 'instructor')
    AND (storage.owner(name) = auth.uid() OR profiles.role = 'admin')
  )
);