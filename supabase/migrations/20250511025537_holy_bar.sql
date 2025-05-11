/*
  # Create materials storage bucket and policies

  1. Storage Setup
    - Create materials bucket with 50MB limit
    - Set allowed file types (PDF, DOCX, TXT)
    - Configure bucket as private

  2. Security Policies
    - Allow authenticated users to read materials
    - Allow admins and instructors to upload materials
    - Allow admins and instructors to delete their own materials
*/

-- Create the materials bucket
SELECT storage.create_bucket('materials', '{"public": false}');

-- Create policy for reading materials
SELECT storage.create_policy(
  'materials',
  'read_materials',
  'SELECT',
  'authenticated',
  '',
  true
);

-- Create policy for uploading materials
SELECT storage.create_policy(
  'materials',
  'upload_materials',
  'INSERT',
  'authenticated',
  '',
  EXISTS (
    SELECT 1 FROM profiles
    WHERE profiles.id = auth.uid()
    AND profiles.role IN ('admin', 'instructor')
  )
);

-- Create policy for deleting materials
SELECT storage.create_policy(
  'materials',
  'delete_materials',
  'DELETE',
  'authenticated',
  '',
  EXISTS (
    SELECT 1 FROM profiles
    WHERE profiles.id = auth.uid()
    AND profiles.role IN ('admin', 'instructor')
  )
);

-- Set bucket configuration
UPDATE storage.buckets
SET file_size_limit = 52428800, -- 50MB
    allowed_mime_types = ARRAY[
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ]
WHERE id = 'materials';