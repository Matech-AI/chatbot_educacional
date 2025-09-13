# Guia de Autenticação com Supabase

Este documento explica como usar o novo sistema de autenticação integrado com Supabase no projeto DNA da Força AI.

## Visão Geral

O sistema agora oferece duas opções de autenticação:
1. **Sistema Local** (legado) - Baseado em arquivos JSON locais
2. **Sistema Supabase** (novo) - Baseado em banco de dados PostgreSQL com autenticação segura

## Configuração do Supabase

### 1. Variáveis de Ambiente

Adicione as seguintes variáveis ao seu arquivo `.env`:

```env
# Supabase Configuration
VITE_SUPABASE_URL=https://seu-projeto.supabase.co
VITE_SUPABASE_ANON_KEY=sua-chave-anonima
SUPABASE_SERVICE_ROLE_KEY=sua-service-role-key
```

### 2. Configuração do Banco de Dados

Execute o script SQL em `supabase/migrations/bd_forca_ai.sql` no seu projeto Supabase para criar as tabelas necessárias.

## Endpoints da API

### Autenticação Básica

#### POST `/auth/supabase/signup`
Registra um novo usuário.

**Request:**
```json
{
  "email": "usuario@exemplo.com",
  "password": "senha123",
  "full_name": "Nome Completo",
  "role": "student"
}
```

**Response:**
```json
{
  "message": "Usuário criado com sucesso",
  "user_id": "uuid-do-usuario",
  "email": "usuario@exemplo.com"
}
```

#### POST `/auth/supabase/signin`
Autentica um usuário existente.

**Request:**
```json
{
  "email": "usuario@exemplo.com",
  "password": "senha123"
}
```

**Response:**
```json
{
  "message": "Login realizado com sucesso",
  "user": {
    "id": "uuid-do-usuario",
    "email": "usuario@exemplo.com",
    "role": "student",
    "full_name": "Nome Completo"
  },
  "session": {
    "access_token": "jwt-token",
    "refresh_token": "refresh-token",
    "expires_at": "2024-01-01T00:00:00Z"
  }
}
```

#### POST `/auth/supabase/signout`
Desconecta o usuário atual.

**Response:**
```json
{
  "message": "Logout realizado com sucesso"
}
```

#### GET `/auth/supabase/me`
Retorna dados do usuário atual.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user": {
    "id": "uuid-do-usuario",
    "email": "usuario@exemplo.com",
    "role": "student",
    "full_name": "Nome Completo",
    "avatar_url": "url-do-avatar",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### Gerenciamento de Perfil

#### PUT `/auth/supabase/profile`
Atualiza perfil do usuário atual.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "full_name": "Novo Nome",
  "avatar_url": "nova-url-do-avatar"
}
```

#### PUT `/auth/supabase/password`
Atualiza senha do usuário atual.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "current_password": "senha-atual",
  "new_password": "nova-senha"
}
```

#### POST `/auth/supabase/reset-password`
Envia email de reset de senha.

**Request:**
```json
{
  "email": "usuario@exemplo.com"
}
```

### Endpoints Administrativos

#### POST `/auth/supabase/admin/users`
Cria usuário (apenas administradores).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request:**
```json
{
  "email": "usuario@exemplo.com",
  "password": "senha123",
  "full_name": "Nome Completo",
  "role": "student"
}
```

#### GET `/auth/supabase/admin/users`
Lista todos os usuários (apenas administradores).

**Headers:**
```
Authorization: Bearer <admin_token>
```

#### PUT `/auth/supabase/admin/users/{user_id}/role`
Atualiza role do usuário (apenas administradores).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request:**
```json
{
  "role": "instructor"
}
```

#### DELETE `/auth/supabase/admin/users/{user_id}`
Remove usuário (apenas administradores).

**Headers:**
```
Authorization: Bearer <admin_token>
```

## Uso no Frontend

### Configuração do Cliente Supabase

```typescript
import { supabase } from './lib/supabase'

// Registrar usuário
const { data, error } = await supabase.auth.signUp({
  email: 'usuario@exemplo.com',
  password: 'senha123',
  options: {
    data: {
      full_name: 'Nome Completo',
      role: 'student'
    }
  }
})

// Fazer login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'usuario@exemplo.com',
  password: 'senha123'
})

// Fazer logout
await supabase.auth.signOut()

// Obter usuário atual
const { data: { user } } = await supabase.auth.getUser()
```

### Store de Autenticação

Use o store `useSupabaseAuthStore` para gerenciar o estado de autenticação:

```typescript
import { useSupabaseAuthStore } from './store/supabase-auth-store'

const { 
  isAuthenticated, 
  user, 
  signIn, 
  signOut, 
  signUp 
} = useSupabaseAuthStore()
```

## Migração de Dados

### Script de Migração

Execute o script de migração para transferir usuários do sistema local para o Supabase:

```bash
cd backend
python scripts/migrate_users_to_supabase.py
```

### Backup dos Dados Locais

Antes da migração, faça backup dos arquivos:
- `backend/data/users_db.json`
- `backend/data/approved_users.json`
- `backend/data/auth_tokens.json`

## Segurança

### Row Level Security (RLS)

O Supabase implementa RLS nas seguintes tabelas:
- `profiles` - Usuários só podem ver/editar seu próprio perfil
- `materials` - Controle baseado em roles (admin, instructor, student)
- `chat_sessions` - Usuários só podem acessar suas próprias sessões
- `chat_messages` - Usuários só podem acessar mensagens de suas sessões

### Políticas de Acesso

- **Admin**: Acesso total ao sistema
- **Instructor**: Pode criar/editar materiais e gerenciar sessões de chat
- **Student**: Acesso limitado a materiais e suas próprias sessões

## Troubleshooting

### Problemas Comuns

1. **Erro de conexão com Supabase**
   - Verifique as variáveis de ambiente
   - Confirme se o projeto Supabase está ativo

2. **Usuário não encontrado após login**
   - Verifique se o perfil foi criado na tabela `profiles`
   - Execute o script de migração se necessário

3. **Permissões negadas**
   - Verifique se as políticas RLS estão configuradas corretamente
   - Confirme se o usuário tem o role correto

### Logs

Monitore os logs do backend para identificar problemas:
```bash
tail -f backend/logs/app.log
```

## Próximos Passos

1. Configure as variáveis de ambiente
2. Execute a migração do banco de dados
3. Teste os endpoints de autenticação
4. Migre os usuários existentes
5. Atualize o frontend para usar o novo sistema
6. Desative o sistema de autenticação local (opcional)

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs do sistema
2. Consulte a documentação do Supabase
3. Abra uma issue no repositório do projeto
