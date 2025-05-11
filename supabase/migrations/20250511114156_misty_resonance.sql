/*
  # Fix Storage Policies for Materials

  1. Changes
    - Create storage bucket for materials if it doesn't exist
    - Enable row level security on the bucket
    - Add policies for file operations:
      - Admins and instructors can upload files
      - All authenticated users can download/view files
      - Admins and instructors can delete their own files

  2. Security
    - Enforces role-based access control through RLS policies
    - Restricts file operations based on user roles
    - Ensures uploaded files are associated with the uploader
*/

-- Create materials bucket if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM storage.buckets WHERE id = 'materials'
  ) THEN
    INSERT INTO storage.buckets (id, name)
    VALUES ('materials', 'materials');
  END IF;
END $$;

-- Enable RLS
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "Allow admin and instructor uploads" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated downloads" ON storage.objects;
DROP POLICY IF EXISTS "Allow admin and instructor deletes" ON storage.objects;

-- Policy for file uploads
CREATE POLICY "Allow admin and instructor uploads"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'materials'
  AND (
    EXISTS (
      SELECT 1 FROM auth.users
      JOIN public.profiles ON profiles.id = auth.users.id
      WHERE auth.users.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
    )
  )
);

-- Policy for file downloads/viewing
CREATE POLICY "Allow authenticated downloads"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'materials');

-- Policy for file deletions
CREATE POLICY "Allow admin and instructor deletes"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id = 'materials'
  AND (
    EXISTS (
      SELECT 1 FROM auth.users
      JOIN public.profiles ON profiles.id = auth.users.id
      WHERE auth.users.id = auth.uid()
      AND (
        profiles.role = 'admin'
        OR (profiles.role = 'instructor' AND storage.objects.owner = auth.uid())
      )
    )
  )
);