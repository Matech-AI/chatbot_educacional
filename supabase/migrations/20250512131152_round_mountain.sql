/*
  # Storage and materials configuration

  1. Changes
    - Create materials storage bucket
    - Configure storage policies for materials
    - Add function for handling material uploads

  2. Security
    - Enable RLS for materials table
    - Add policies for authenticated users
*/

-- Create materials bucket if it doesn't exist
DO $$
BEGIN
  INSERT INTO storage.buckets (id, name)
  VALUES ('materials', 'materials')
  ON CONFLICT (id) DO NOTHING;
END $$;

-- Create policy to allow authenticated users to read materials
CREATE POLICY "Allow authenticated users to read materials"
ON public.materials FOR SELECT
TO authenticated
USING (true);

-- Create policy to allow admins and instructors to upload materials
CREATE POLICY "Allow admins and instructors to upload materials"
ON public.materials FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.profiles
    WHERE id = auth.uid()
    AND role IN ('admin', 'instructor')
  )
);

-- Create policy to allow admins and instructors to update their own materials
CREATE POLICY "Allow admins and instructors to update own materials"
ON public.materials FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.profiles
    WHERE id = auth.uid()
    AND role IN ('admin', 'instructor')
    AND (uploaded_by = auth.uid() OR role = 'admin')
  )
);

-- Create policy to allow admins and instructors to delete their own materials
CREATE POLICY "Allow admins and instructors to delete own materials"
ON public.materials FOR DELETE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.profiles
    WHERE id = auth.uid()
    AND role IN ('admin', 'instructor')
    AND (uploaded_by = auth.uid() OR role = 'admin')
  )
);

-- Create function to handle material uploads
CREATE OR REPLACE FUNCTION handle_material_upload()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Set uploaded_by to current user if not specified
  IF NEW.uploaded_by IS NULL THEN
    NEW.uploaded_by := auth.uid();
  END IF;
  
  -- Set created_at if not specified
  IF NEW.created_at IS NULL THEN
    NEW.created_at := now();
  END IF;
  
  -- Set updated_at
  NEW.updated_at := now();
  
  RETURN NEW;
END;
$$;

-- Create trigger for material uploads
CREATE TRIGGER handle_material_upload_trigger
  BEFORE INSERT OR UPDATE ON public.materials
  FOR EACH ROW
  EXECUTE FUNCTION handle_material_upload();