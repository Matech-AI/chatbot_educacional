/*
  # Add Storage Policies for Materials Bucket

  1. Changes
    - Add storage policies for the materials bucket to allow:
      - Authenticated users to read files
      - Authenticated users to upload files
      - Users to delete their own files
      
  2. Security
    - Enable RLS on storage.objects table for materials bucket
    - Add policies for read, insert, and delete operations
*/

-- Enable RLS for storage
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read any file in the materials bucket
CREATE POLICY "Allow authenticated read access"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'materials');

-- Allow authenticated users to upload files to materials bucket
CREATE POLICY "Allow authenticated insert access"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'materials');

-- Allow users to delete their own files
CREATE POLICY "Allow users to delete own files"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'materials' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

-- Update materials upload function to store files in user-specific folders
CREATE OR REPLACE FUNCTION storage.foldername(name text)
RETURNS text[]
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN string_to_array(trim(both '/' from name), '/');
END
$$;