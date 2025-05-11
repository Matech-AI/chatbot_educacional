/*
  # Create storage bucket for materials and set up policies

  1. Storage Configuration
    - Create materials bucket
    - Set file size limit to 50MB
    - Set allowed MIME types for documents
  
  2. Security
    - Enable RLS
    - Add policies for:
      - Reading (all authenticated users)
      - Uploading (admins and instructors only)
      - Deleting (admins and instructors only)
*/

-- Create the materials bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('materials', 'materials', false)
ON CONFLICT (id) DO NOTHING;

-- Enable RLS
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Set bucket configuration
UPDATE storage.buckets
SET file_size_limit = 52428800, -- 50MB
    allowed_mime_types = ARRAY[
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'video/mp4',
      'video/webm',
      'video/quicktime'
    ]
WHERE id = 'materials';

-- Create policy for reading materials
CREATE POLICY "Authenticated users can read materials"
  ON storage.objects
  FOR SELECT
  TO authenticated
  USING (bucket_id = 'materials');

-- Create policy for uploading materials
CREATE POLICY "Admins and instructors can upload materials"
  ON storage.objects
  FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'materials'
    AND EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
    )
  );

-- Create policy for deleting materials
CREATE POLICY "Admins and instructors can delete materials"
  ON storage.objects
  FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'materials'
    AND EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
      AND (owner = auth.uid() OR profiles.role = 'admin')
    )
  );