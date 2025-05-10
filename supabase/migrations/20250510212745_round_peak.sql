/*
  # DNA da Força Database Schema

  1. Tables
    - profiles (user profiles)
    - materials (training materials)
    - assistant_configs (AI assistant settings)
    - assistant_templates (reusable configurations)
    - chat_sessions (user chat sessions)
    - chat_messages (individual chat messages)

  2. Security
    - Row Level Security (RLS) enabled on all tables
    - Role-based access policies
    - User-specific data protection
*/

-- Create updated_at trigger function if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at') THEN
    CREATE FUNCTION update_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
      NEW.updated_at = now();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
  END IF;
END $$;

-- Profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  full_name text NOT NULL,
  role text NOT NULL CHECK (role IN ('admin', 'instructor', 'student')),
  avatar_url text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Materials table
CREATE TABLE IF NOT EXISTS materials (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  description text,
  type text NOT NULL,
  path text NOT NULL,
  size bigint NOT NULL,
  tags text[] DEFAULT '{}',
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

-- Chat Sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
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

-- Drop existing policies to avoid conflicts
DO $$ 
BEGIN
  -- Profiles policies
  DROP POLICY IF EXISTS "Users can read own profile" ON profiles;
  DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
  
  -- Materials policies
  DROP POLICY IF EXISTS "All users can read materials" ON materials;
  DROP POLICY IF EXISTS "Admins and instructors can insert materials" ON materials;
  DROP POLICY IF EXISTS "Admins and instructors can update own materials" ON materials;
  DROP POLICY IF EXISTS "Admins and instructors can delete own materials" ON materials;
  
  -- Assistant configs policies
  DROP POLICY IF EXISTS "Everyone can read assistant configs" ON assistant_configs;
  DROP POLICY IF EXISTS "Admins and instructors can insert assistant configs" ON assistant_configs;
  DROP POLICY IF EXISTS "Admins and instructors can update assistant configs" ON assistant_configs;
  
  -- Assistant templates policies
  DROP POLICY IF EXISTS "Everyone can read templates" ON assistant_templates;
  DROP POLICY IF EXISTS "Admins and instructors can manage templates" ON assistant_templates;
  
  -- Chat sessions policies
  DROP POLICY IF EXISTS "Users can read own chat sessions" ON chat_sessions;
  DROP POLICY IF EXISTS "Users can insert own chat sessions" ON chat_sessions;
  DROP POLICY IF EXISTS "Users can update own chat sessions" ON chat_sessions;
  DROP POLICY IF EXISTS "Users can delete own chat sessions" ON chat_sessions;
  
  -- Chat messages policies
  DROP POLICY IF EXISTS "Users can read messages from own sessions" ON chat_messages;
  DROP POLICY IF EXISTS "Users can insert messages to own sessions" ON chat_messages;
END $$;

-- Recreate all policies
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

-- Create triggers if they don't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_profiles_updated_at') THEN
    CREATE TRIGGER update_profiles_updated_at
      BEFORE UPDATE ON profiles
      FOR EACH ROW
      EXECUTE FUNCTION update_updated_at();
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_materials_updated_at') THEN
    CREATE TRIGGER update_materials_updated_at
      BEFORE UPDATE ON materials
      FOR EACH ROW
      EXECUTE FUNCTION update_updated_at();
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_assistant_configs_updated_at') THEN
    CREATE TRIGGER update_assistant_configs_updated_at
      BEFORE UPDATE ON assistant_configs
      FOR EACH ROW
      EXECUTE FUNCTION update_updated_at();
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_chat_sessions_updated_at') THEN
    CREATE TRIGGER update_chat_sessions_updated_at
      BEFORE UPDATE ON chat_sessions
      FOR EACH ROW
      EXECUTE FUNCTION update_updated_at();
  END IF;
END $$;