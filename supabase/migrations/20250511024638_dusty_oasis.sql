/*
  # Add Google Drive integration

  1. New Tables
    - `drive_credentials`
      - `id` (uuid, primary key)
      - `credentials` (jsonb)
      - `created_by` (uuid, references profiles)
      - `created_at` (timestamp)
      - `is_active` (boolean)

  2. Security
    - Enable RLS on drive_credentials table
    - Add policies for admins and instructors
*/

-- Create drive_credentials table
CREATE TABLE IF NOT EXISTS drive_credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  credentials JSONB NOT NULL,
  created_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  is_active BOOLEAN DEFAULT true
);

-- Enable RLS
ALTER TABLE drive_credentials ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Admins and instructors can manage drive credentials"
  ON drive_credentials
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
    )
  );

-- Insert initial credentials
INSERT INTO drive_credentials (credentials, is_active)
VALUES (
  '{
    "web": {
      "client_id": "405717380359-hevec8ueh9gbithso2aeavmfop4g17q3.apps.googleusercontent.com",
      "project_id": "chatbot-educacao-fisica-ai",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_secret": "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"
    }
  }'::jsonb,
  true
);