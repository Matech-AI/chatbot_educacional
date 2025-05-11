/*
  # Configure storage bucket for materials

  1. Storage Configuration
    - Create materials bucket for storing course materials
    - Set file size limit to 50MB
    - Allow only specific file types (PDF, DOCX, TXT)
    - Configure bucket-level security policies

  2. Security
    - Enable bucket-level security
    - Add policies for authenticated users
*/

-- Create a secure bucket for materials
BEGIN;

-- Insert the bucket if it doesn't exist
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'materials',
  'materials',
  false,
  52428800, -- 50MB limit
  ARRAY[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
  ]
) ON CONFLICT (id) DO NOTHING;

-- Create security policies
DO $$
BEGIN
  -- View policy
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'objects' 
    AND policyname = 'Materials Bucket Select Policy'
  ) THEN
    CREATE POLICY "Materials Bucket Select Policy"
      ON storage.objects FOR SELECT
      TO authenticated
      USING (bucket_id = 'materials');
  END IF;

  -- Insert policy
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'objects' 
    AND policyname = 'Materials Bucket Insert Policy'
  ) THEN
    CREATE POLICY "Materials Bucket Insert Policy"
      ON storage.objects FOR INSERT
      TO authenticated
      WITH CHECK (bucket_id = 'materials');
  END IF;

  -- Update policy
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'objects' 
    AND policyname = 'Materials Bucket Update Policy'
  ) THEN
    CREATE POLICY "Materials Bucket Update Policy"
      ON storage.objects FOR UPDATE
      TO authenticated
      USING (bucket_id = 'materials');
  END IF;

  -- Delete policy
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'objects' 
    AND policyname = 'Materials Bucket Delete Policy'
  ) THEN
    CREATE POLICY "Materials Bucket Delete Policy"
      ON storage.objects FOR DELETE
      TO authenticated
      USING (bucket_id = 'materials');
  END IF;
END $$;

COMMIT;