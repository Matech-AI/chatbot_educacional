/*
  # Fix storage policies for materials bucket

  1. Changes
    - Add proper RLS policies for materials bucket
    - Ensure only admins and instructors can upload/modify files
    - Allow all authenticated users to read files

  2. Security
    - Enable RLS on storage bucket
    - Add role-based policies
*/

-- Recreate the materials bucket with proper settings
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'materials',
  'materials',
  false,
  52428800, -- 50MB limit
  ARRAY[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/vnd.google-apps.document'
  ]
) ON CONFLICT (id) DO UPDATE SET
  public = false,
  file_size_limit = 52428800,
  allowed_mime_types = ARRAY[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/vnd.google-apps.document'
  ];

-- Drop existing policies
DROP POLICY IF EXISTS "Materials Bucket Select Policy" ON storage.objects;
DROP POLICY IF EXISTS "Materials Bucket Insert Policy" ON storage.objects;
DROP POLICY IF EXISTS "Materials Bucket Update Policy" ON storage.objects;
DROP POLICY IF EXISTS "Materials Bucket Delete Policy" ON storage.objects;

-- Create new policies with proper role checks
CREATE POLICY "Anyone can read materials"
  ON storage.objects FOR SELECT
  TO authenticated
  USING (bucket_id = 'materials');

CREATE POLICY "Only admins and instructors can upload materials"
  ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'materials' AND
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
    )
  );

CREATE POLICY "Only admins and instructors can update materials"
  ON storage.objects FOR UPDATE
  TO authenticated
  USING (
    bucket_id = 'materials' AND
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
    )
  );

CREATE POLICY "Only admins and instructors can delete materials"
  ON storage.objects FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'materials' AND
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
    )
  );