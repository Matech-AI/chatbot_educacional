/*
  # Add training materials from DNA da Força

  1. Insert Materials
    - Add initial training materials from Google Drive
    - Set proper metadata and tags
    - Link to admin user

  2. Security
    - Maintain existing RLS policies
    - Ensure proper access control
*/

-- Insert training materials (using admin user as uploader)
INSERT INTO materials (
  title,
  description,
  type,
  path,
  size,
  tags,
  uploaded_by,
  created_at
)
SELECT
  data.title,
  data.description,
  data.type,
  data.path,
  data.size,
  data.tags,
  (SELECT id FROM profiles WHERE role = 'admin' LIMIT 1),
  now()
FROM (
  VALUES
    (
      'Fundamentos do Treinamento de Força',
      'Guia completo sobre os princípios básicos e avançados do treinamento de força',
      'pdf',
      'https://drive.google.com/uc?export=download&id=1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ',
      2500000,
      ARRAY['força', 'fundamentos', 'treino']
    ),
    (
      'Periodização do Treinamento',
      'Metodologia detalhada para periodização de treinos de força',
      'pdf',
      'https://drive.google.com/uc?export=download&id=1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ',
      1800000,
      ARRAY['periodização', 'planejamento', 'treino']
    ),
    (
      'Nutrição para Hipertrofia',
      'Guia nutricional focado em ganho de massa muscular',
      'pdf',
      'https://drive.google.com/uc?export=download&id=1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ',
      3200000,
      ARRAY['nutrição', 'hipertrofia', 'suplementação']
    )
) AS data(title, description, type, path, size, tags);