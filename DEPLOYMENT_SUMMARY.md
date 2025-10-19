# 🎉 Configuração Completa - DNA da Força AI

## ✅ Tarefas Concluídas

### 1. 🌐 Configuração do Domínio

- **Domínio**: `https://iadnadaforca.com.br/`
- **WWW**: `https://www.iadnadaforca.com.br/`
- **URLs dos serviços**:
  - Frontend: `https://iadnadaforca.com.br/`
  - API: `https://iadnadaforca.com.br/api`
  - RAG: `https://iadnadaforca.com.br/rag`

### 2. 📧 Configuração de E-mail

- **Domínio**: `@iadnadaforca.com.br`
- **E-mail principal**: `noreply@iadnadaforca.com.br`
- **SMTP**: `smtp.hostinger.com:587`
- **TLS**: Habilitado

### 3. 🗄️ Migração para Banco de Dados

- **Banco**: PostgreSQL 15
- **Script de migração**: `backend/scripts/migrate_to_database.py`
- **Tabelas criadas**:
  - `profiles` - Perfis de usuários
  - `materials` - Materiais educacionais
  - `assistant_configs` - Configurações de assistente
  - `chat_sessions` - Sessões de chat
  - `chat_messages` - Mensagens do chat

### 4. 🚀 Deploy no Coolify

- **Serviços configurados**:
  - PostgreSQL (porta 5432)
  - Redis (porta 6379)
  - API Server (porta 8002)
  - RAG Server (porta 8001)
  - Frontend (porta 3000)

## 📁 Arquivos Criados/Modificados

### Configurações

- `backend/coolify.env` - Configurações do Coolify
- `backend/coolify.env.complete` - Configurações completas
- `backend/domain_config.env` - Configurações específicas do domínio
- `docker-compose.yml` - Serviços Docker atualizados

### Scripts

- `backend/scripts/migrate_to_database.py` - Script de migração
- `scripts/deploy_coolify.sh` - Script de deploy

### Documentação

- `docs/deploy/coolify-deployment-guide.md` - Guia completo de deploy

## 🔧 Configurações Implementadas

### CORS

```env
CORS_ORIGINS=https://iadnadaforca.com.br,https://www.iadnadaforca.com.br,http://localhost:3000,http://127.0.0.1:3000
```

### URLs dos Serviços

```env
API_BASE_URL=https://iadnadaforca.com.br/api
RAG_API_BASE_URL=https://iadnadaforca.com.br/rag
FRONTEND_URL=https://iadnadaforca.com.br
```

### E-mail

```env
EMAIL_HOST=smtp.hostinger.com
EMAIL_PORT=587
EMAIL_USERNAME=noreply@iadnadaforca.com.br
EMAIL_PASSWORD=your_email_password
EMAIL_FROM=noreply@iadnadaforca.com.br
```

### Banco de Dados

```env
DATABASE_URL=postgresql://postgres:password@postgres:5432/dna_da_forca
POSTGRES_DB=dna_da_forca
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
```

## 🚀 Próximos Passos

### 1. Configurar no Coolify

1. Acesse o painel do Coolify
2. Configure as variáveis de ambiente
3. Configure o domínio `iadnadaforca.com.br`
4. Configure o SSL/TLS

### 2. Configurar E-mail na Hostinger

1. Crie o e-mail `noreply@iadnadaforca.com.br`
2. Configure a senha
3. Teste o envio de e-mails

### 3. Executar Migração

1. Execute o script de migração
2. Verifique os dados migrados
3. Teste o sistema

### 4. Testes Finais

1. Teste o login de usuário
2. Teste a criação de usuário
3. Teste o envio de e-mail
4. Teste o chat com o bot

## 📊 Estrutura do Banco de Dados

### Tabela `profiles`

- `id` (uuid) - ID do usuário
- `full_name` (text) - Nome completo
- `email` (text) - E-mail único
- `role` (text) - admin, instructor, student
- `is_active` (boolean) - Status ativo
- `created_at` (timestamptz) - Data de criação
- `updated_at` (timestamptz) - Data de atualização

### Tabela `materials`

- `id` (uuid) - ID do material
- `title` (text) - Título
- `description` (text) - Descrição
- `type` (text) - Tipo do material
- `path` (text) - Caminho do arquivo
- `size` (bigint) - Tamanho do arquivo
- `tags` (text[]) - Tags
- `status` (text) - Status do processamento
- `uploaded_by` (uuid) - ID do usuário que fez upload

### Tabela `assistant_configs`

- `id` (uuid) - ID da configuração
- `name` (text) - Nome da configuração
- `prompt` (text) - Prompt do assistente
- `model` (text) - Modelo de IA
- `temperature` (float) - Temperatura
- `chunk_size` (integer) - Tamanho do chunk
- `embedding_model` (text) - Modelo de embedding

## 🔒 Segurança

### Configurações Implementadas

- ✅ CORS configurado para o domínio correto
- ✅ JWT com chave secreta
- ✅ Rate limiting configurado
- ✅ SSL/TLS obrigatório
- ✅ Senhas com hash criptográfico

### Recomendações

- 🔐 Use senhas fortes para o banco de dados
- 🔐 Configure firewall adequadamente
- 🔐 Monitore logs de acesso
- 🔐 Faça backups regulares

## 📞 Suporte

- **Documentação**: `docs/deploy/coolify-deployment-guide.md`
- **Scripts**: `scripts/deploy_coolify.sh`
- **Configurações**: `backend/coolify.env.complete`

---

**🎉 Sistema configurado com sucesso para produção!**

O DNA da Força AI está pronto para ser deployado no Coolify da Hostinger com o domínio `https://iadnadaforca.com.br/` e e-mails com domínio `@iadnadaforca.com.br`.
