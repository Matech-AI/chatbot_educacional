/*
  # Set up storage bucket for materials

  1. Storage Setup
    - Create materials bucket if it doesn't exist
    - Set file size limit to 50MB
    - Allow specific file types (PDF, DOCX, TXT, Google Docs)

  2. Security
    - Drop existing policies if they exist
    - Create new policies for authenticated users
    - Enable CRUD operations on materials bucket
*/

-- Create storage bucket for materials if it doesn't exist
INSERT INTO storage.buckets (id, name, public, avif_autodetection, file_size_limit, allowed_mime_types)
VALUES (
  'materials',
  'materials',
  false,
  false,
  52428800, -- 50MB limit
  ARRAY[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/vnd.google-apps.document'
  ]
) ON CONFLICT (id) DO NOTHING;

-- Drop existing policies if they exist
DO $$ 
BEGIN
  DROP POLICY IF EXISTS "Authenticated users can view materials" ON storage.objects;
  DROP POLICY IF EXISTS "Authenticated users can upload materials" ON storage.objects;
  DROP POLICY IF EXISTS "Authenticated users can update materials" ON storage.objects;
  DROP POLICY IF EXISTS "Authenticated users can delete materials" ON storage.objects;
EXCEPTION
  WHEN undefined_object THEN
    NULL;
END $$;

-- Create new storage policies
CREATE POLICY "Authenticated users can view materials"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'materials');

CREATE POLICY "Authenticated users can upload materials"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'materials');

CREATE POLICY "Authenticated users can update materials"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'materials');

CREATE POLICY "Authenticated users can delete materials"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'materials');