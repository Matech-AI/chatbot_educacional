/*
  # Initial database schema for EduAssistant AI

  1. New Tables
    - `profiles` - User profiles and roles
    - `materials` - Educational materials
    - `assistant_configs` - AI assistant configurations
    - `assistant_templates` - Reusable assistant templates
    - `chat_sessions` - User chat sessions
    - `chat_messages` - Individual chat messages

  2. Security
    - Enable RLS on all tables
    - Add appropriate policies for each role
    - Set up necessary triggers
*/

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Profiles table
DROP TABLE IF EXISTS profiles CASCADE;
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  full_name text NOT NULL,
  email text NOT NULL UNIQUE,
  role text NOT NULL CHECK (role IN ('admin', 'instructor', 'student')),
  avatar_url text,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Materials table
DROP TABLE IF EXISTS materials CASCADE;
CREATE TABLE IF NOT EXISTS materials (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  description text,
  type text NOT NULL CHECK (type IN ('text', 'video', 'data', 'image', 'document', 'research_paper')),
  path text NOT NULL,
  original_filename text,
  size bigint NOT NULL,
  tags text[] DEFAULT '{}',
  status text NOT NULL DEFAULT 'pending', -- pending, processed, error
  uploaded_by uuid REFERENCES profiles(id) ON DELETE SET NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE materials ENABLE ROW LEVEL SECURITY;

-- Assistant Configurations
CREATE TABLE IF NOT EXISTS assistant_configs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  prompt text NOT NULL,
  model text NOT NULL,
  temperature float NOT NULL DEFAULT 0.7,
  chunk_size integer NOT NULL DEFAULT 2000,
  chunk_overlap integer NOT NULL DEFAULT 200,
  retrieval_search_type text NOT NULL DEFAULT 'similarity',
  embedding_model text NOT NULL DEFAULT 'text-embedding-ada-002',
  created_by uuid REFERENCES profiles(id) ON DELETE SET NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE assistant_configs ENABLE ROW LEVEL SECURITY;

-- Assistant Templates
CREATE TABLE IF NOT EXISTS assistant_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  config jsonb NOT NULL,
  created_by uuid REFERENCES profiles(id) ON DELETE SET NULL,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE assistant_templates ENABLE ROW LEVEL SECURITY;

-- Chat Sessions table
DROP TABLE IF EXISTS chat_sessions CASCADE;
CREATE TABLE IF NOT EXISTS chat_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  assistant_id uuid REFERENCES assistant_configs(id) ON DELETE SET NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

-- Chat Messages
CREATE TABLE IF NOT EXISTS chat_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid REFERENCES chat_sessions(id) ON DELETE CASCADE,
  content text NOT NULL,
  role text NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  sources jsonb,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can read own profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id);

-- Materials policies
CREATE POLICY "All users can read materials"
  ON materials FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins and instructors can insert materials"
  ON materials FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
    )
  );

CREATE POLICY "Admins and instructors can update own materials"
  ON materials FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
      AND (uploaded_by = auth.uid() OR profiles.role = 'admin')
    )
  );

CREATE POLICY "Admins and instructors can delete own materials"
  ON materials FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
      AND (uploaded_by = auth.uid() OR profiles.role = 'admin')
    )
  );

-- Assistant configs policies
CREATE POLICY "Everyone can read assistant configs"
  ON assistant_configs FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins and instructors can insert assistant configs"
  ON assistant_configs FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
    )
  );

CREATE POLICY "Admins and instructors can update assistant configs"
  ON assistant_configs FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
    )
  );

-- Assistant templates policies
CREATE POLICY "Everyone can read templates"
  ON assistant_templates FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins and instructors can manage templates"
  ON assistant_templates
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('admin', 'instructor')
    )
  );

-- Chat sessions policies
CREATE POLICY "Users can read own chat sessions"
  ON chat_sessions FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Users can insert own chat sessions"
  ON chat_sessions FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own chat sessions"
  ON chat_sessions FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Users can delete own chat sessions"
  ON chat_sessions FOR DELETE
  TO authenticated
  USING (user_id = auth.uid());

-- Chat messages policies
CREATE POLICY "Users can read messages from own sessions"
  ON chat_messages FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM chat_sessions
      WHERE chat_sessions.id = chat_messages.session_id
      AND chat_sessions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert messages to own sessions"
  ON chat_messages FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM chat_sessions
      WHERE chat_sessions.id = session_id
      AND chat_sessions.user_id = auth.uid()
    )
  );

-- Create triggers
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_materials_updated_at
  BEFORE UPDATE ON materials
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_assistant_configs_updated_at
  BEFORE UPDATE ON assistant_configs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_chat_sessions_updated_at
  BEFORE UPDATE ON chat_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();