/*
  # Add API key management and usage tracking

  1. New Tables
    - `api_keys`
      - Stores OpenAI API keys
      - Only admins can access
    - `api_usage`
      - Tracks OpenAI API usage
      - Records cost per request
      
  2. New Functions
    - `get_api_key()`: Retrieves active API key
    - `set_api_key()`: Updates API key (admin only)
    - `track_api_usage()`: Records API usage
*/

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key_value TEXT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- API Usage tracking
CREATE TABLE IF NOT EXISTS api_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_type TEXT NOT NULL,
  tokens_used INTEGER NOT NULL,
  cost_usd DECIMAL(10,6) NOT NULL,
  user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;

-- Function to get active API key
CREATE OR REPLACE FUNCTION get_api_key()
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  RETURN (
    SELECT key_value 
    FROM api_keys 
    WHERE is_active = true 
    ORDER BY created_at DESC 
    LIMIT 1
  );
END;
$$;

-- Function to set API key (admin only)
CREATE OR REPLACE FUNCTION set_api_key(new_key TEXT)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF NOT is_admin() THEN
    RAISE EXCEPTION 'Only administrators can set API keys';
  END IF;

  -- Deactivate current key
  UPDATE api_keys SET is_active = false WHERE is_active = true;

  -- Insert new key
  INSERT INTO api_keys (key_value, created_by)
  VALUES (new_key, auth.uid());
END;
$$;

-- Function to track API usage
CREATE OR REPLACE FUNCTION track_api_usage(
  p_request_type TEXT,
  p_tokens_used INTEGER,
  p_cost_usd DECIMAL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO api_usage (request_type, tokens_used, cost_usd, user_id)
  VALUES (p_request_type, p_tokens_used, p_cost_usd, auth.uid());
END;
$$;

-- Policies for API keys
CREATE POLICY "Only admins can view API keys"
  ON api_keys FOR SELECT
  TO authenticated
  USING (is_admin());

-- Policies for API usage
CREATE POLICY "Users can view own usage"
  ON api_usage FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Admins can view all usage"
  ON api_usage FOR SELECT
  TO authenticated
  USING (is_admin());

-- Comments
COMMENT ON TABLE api_keys IS 'Stores OpenAI API keys';
COMMENT ON TABLE api_usage IS 'Tracks OpenAI API usage and costs';
COMMENT ON FUNCTION get_api_key IS 'Get the currently active API key';
COMMENT ON FUNCTION set_api_key IS 'Set a new API key (admin only)';
COMMENT ON FUNCTION track_api_usage IS 'Record API usage and cost';