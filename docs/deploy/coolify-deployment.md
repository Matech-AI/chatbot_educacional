# Deploy no Coolify - Guia Completo

Este guia explica como fazer o deploy do projeto DNA da Força AI no Coolify usando Docker, com foco especial na configuração do Supabase.

## 📋 Pré-requisitos

1. **Conta no Coolify** configurada
2. **Projeto Supabase** ativo com:
   - URL do projeto
   - Chave anônima (anon key)
   - Chave de serviço (service role key)
3. **Chaves de API** necessárias:
   - OpenAI API Key
   - Outras APIs opcionais (Gemini, NVIDIA, etc.)

## 🔧 Configuração das Variáveis de Ambiente

### 1. Variáveis Obrigatórias do Supabase

No painel do Coolify, configure as seguintes variáveis de ambiente:

```env
# Configurações do Supabase (OBRIGATÓRIAS)
VITE_SUPABASE_URL=https://seu-projeto.supabase.co
VITE_SUPABASE_ANON_KEY=sua_chave_anonima_aqui
SUPABASE_SERVICE_ROLE_KEY=sua_chave_de_servico_aqui

# API Configuration
VITE_API_URL=https://seu-dominio-api.coolify.io
```

### 2. Variáveis de API

```env
# Chaves de API (OBRIGATÓRIAS)
OPENAI_API_KEY=sua_chave_openai_aqui
JWT_SECRET_KEY=sua_chave_jwt_secreta_aqui

# APIs Opcionais
GEMINI_API_KEY=sua_chave_gemini_aqui
NVIDIA_API_KEY=sua_chave_nvidia_aqui
GOOGLE_DRIVE_API_KEY=sua_chave_google_drive_aqui
```

### 3. Configurações do Sistema

```env
# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# CORS Origins (ajuste para seus domínios)
CORS_ORIGINS=https://seu-frontend.coolify.io,https://seu-api.coolify.io

# JWT Configuration
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server Configuration
HOSTINGER=false
SERVER_IP=0.0.0.0
RAG_PORT=5001
API_PORT=5000
FRONTEND_PORT=3000

# RAG Configuration
RAG_SERVER_URL=http://rag-server:5001
CHROMA_PERSIST_DIR=/app/data/.chromadb
MATERIALS_DIR=/app/data/materials
PREFER_OPEN_SOURCE_EMBEDDINGS=true
OPEN_SOURCE_EMBEDDING_MODEL=intfloat/multilingual-e5-large

# Redis (opcional)
REDIS_URL=redis://redis:6379

# Email Configuration (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app
EMAIL_FROM=seu_email@gmail.com
```

## 🚀 Configuração no Coolify

### 1. Criar Novo Projeto

1. Acesse o painel do Coolify
2. Clique em "New Project"
3. Conecte seu repositório GitHub
4. Selecione o branch principal

### 2. Configurar Serviços

#### Frontend Service
- **Nome**: `frontend`
- **Dockerfile**: `Dockerfile.frontend`
- **Porta**: `3000`
- **Build Args**: Configure as variáveis do Supabase como build arguments

#### Backend Service
- **Nome**: `backend`
- **Dockerfile**: `backend/Dockerfile.api`
- **Porta**: `5000`
- **Volumes**: Configure volumes para persistência de dados

#### RAG Server Service
- **Nome**: `rag-server`
- **Dockerfile**: `backend/Dockerfile.rag`
- **Porta**: `5001`

### 3. Configurar Volumes

Crie os seguintes volumes persistentes:

```yaml
volumes:
  chromadb_data: {}
  materials_data: {}
```

### 4. Configurar Rede

Certifique-se de que os serviços podem se comunicar:
- Frontend → Backend (porta 5000)
- Backend → RAG Server (porta 5001)

## 🔍 Troubleshooting

### Erro: "Variáveis de ambiente do Supabase não configuradas"

**Solução:**
1. Verifique se `VITE_SUPABASE_URL` e `VITE_SUPABASE_ANON_KEY` estão configuradas
2. Certifique-se de que as variáveis estão sendo passadas como build args no frontend
3. Reinicie o build do frontend

### Erro: "Failed to connect to Supabase"

**Solução:**
1. Verifique se a URL do Supabase está correta
2. Confirme se o projeto Supabase está ativo
3. Teste a conectividade com o Supabase externamente

### Erro: "Authentication failed"

**Solução:**
1. Verifique se a `SUPABASE_SERVICE_ROLE_KEY` está correta
2. Confirme se as políticas RLS estão configuradas corretamente no Supabase
3. Execute o script SQL de migração: `supabase/migrations/bd_forca_ai.sql`

### Erro: "CORS policy"

**Solução:**
1. Adicione o domínio do Coolify em `CORS_ORIGINS`
2. Configure o CORS no Supabase para aceitar seu domínio
3. Verifique se `VITE_API_URL` aponta para o domínio correto

## 📝 Checklist de Deploy

- [ ] ✅ Variáveis do Supabase configuradas
- [ ] ✅ Chaves de API configuradas
- [ ] ✅ Build args configurados no frontend
- [ ] ✅ Volumes persistentes criados
- [ ] ✅ Rede entre serviços configurada
- [ ] ✅ CORS configurado corretamente
- [ ] ✅ Migração SQL executada no Supabase
- [ ] ✅ Políticas RLS configuradas no Supabase
- [ ] ✅ Teste de conectividade realizado

## 🔗 Links Úteis

- [Documentação do Coolify](https://coolify.io/docs)
- [Documentação do Supabase](https://supabase.com/docs)
- [Guia de Autenticação Supabase](../authentication/supabase-auth-guide.md)

## 📞 Suporte

Se você encontrar problemas durante o deploy:

1. Verifique os logs do Coolify para cada serviço
2. Teste a conectividade com o Supabase
3. Confirme se todas as variáveis de ambiente estão configuradas
4. Consulte a documentação específica do erro

---

**Nota**: Este guia assume que você já tem um projeto Supabase configurado. Se não tiver, consulte o [Guia de Configuração do Supabase](../authentication/supabase-auth-guide.md) primeiro.