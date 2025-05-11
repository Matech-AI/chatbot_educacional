/*
  # Fix storage bucket policies for materials

  1. Changes
    - Create materials storage bucket if it doesn't exist
    - Enable RLS on the bucket
    - Add policies for:
      - Admins and instructors can upload files
      - All authenticated users can download files
      - File size and type restrictions
*/

-- Create the materials bucket if it doesn't exist
DO $$
BEGIN
  INSERT INTO storage.buckets (id, name, public)
  VALUES ('materials', 'materials', false)
  ON CONFLICT (id) DO NOTHING;
END $$;

-- Enable RLS on the bucket
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Allow admins and instructors to upload files
CREATE POLICY "Admins and instructors can upload materials"
  ON storage.objects
  FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'materials'
    AND (
      EXISTS (
        SELECT 1 FROM profiles
        WHERE profiles.id = auth.uid()
        AND profiles.role IN ('admin', 'instructor')
      )
    )
    -- Restrict file types to PDF, DOCX, TXT, and common video formats
    AND (
      lower(storage.extension(name)) = ANY (ARRAY['pdf', 'docx', 'txt', 'mp4', 'webm', 'mov'])
    )
    -- Limit file size to 100MB
    AND (octet_length(content) <= 104857600)
  );

-- Allow authenticated users to read files
CREATE POLICY "Authenticated users can read materials"
  ON storage.objects
  FOR SELECT
  TO authenticated
  USING (bucket_id = 'materials');

-- Allow admins and instructors to delete their own files
CREATE POLICY "Admins and instructors can delete own materials"
  ON storage.objects
  FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'materials'
    AND (
      EXISTS (
        SELECT 1 FROM profiles
        WHERE profiles.id = auth.uid()
        AND profiles.role IN ('admin', 'instructor')
        AND (owner = auth.uid() OR profiles.role = 'admin')
      )
    )
  );