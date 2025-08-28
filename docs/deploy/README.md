# 🚀 Guia de Deploy Completo - Sistema RAG DNA da Força

Este guia abrange todas as opções de deploy disponíveis para o Sistema RAG DNA da Força, desde deploy local até plataformas em nuvem.

## 📋 **Pré-requisitos**

### **Requisitos do Sistema:**

- **Python 3.8+**
- **Node.js 16+**
- **8GB RAM mínimo**
- **50GB espaço em disco**
- **Conexão com internet estável**

### **Contas Necessárias:**

- [OpenAI](https://platform.openai.com/) ou [Anthropic](https://console.anthropic.com/) para IA
- [Supabase](https://supabase.com/) para autenticação
- [Google Cloud](https://cloud.google.com/) para Google Drive API
- Plataforma de deploy escolhida (Render, Hostinger, etc.)

## 🎯 **Opções de Deploy**

### **1. 🐳 Deploy com Docker (Recomendado)**

- **Vantagens:** Consistente, isolado, fácil de replicar
- **Complexidade:** Média
- **Custo:** Baixo
- **Tempo:** 30-60 minutos

[📖 Guia Docker Completo](docker-deployment.md)

### **2. ☁️ Deploy no Render (Mais Fácil)**

- **Vantagens:** Automático, gratuito, integração com GitHub
- **Complexidade:** Baixa
- **Custo:** Gratuito para uso básico
- **Tempo:** 15-30 minutos

[📖 Guia Render Completo](render-deployment.md)

### **3. 🌐 Deploy no Hostinger (Alternativa)**

- **Vantagens:** Controle total, hospedagem compartilhada
- **Complexidade:** Média
- **Custo:** Baixo
- **Tempo:** 45-90 minutos

[📖 Guia Hostinger Completo](hostinger-deployment.md)

### **4. 💻 Deploy Local (Desenvolvimento)**

- **Vantagens:** Controle total, sem custos
- **Complexidade:** Baixa
- **Custo:** Zero
- **Tempo:** 15-30 minutos

[📖 Guia Desenvolvimento Local](../development/local-development.md)

## 🔧 **Configuração Inicial**

### **1. Clone o Repositório**

```bash
git clone https://github.com/seu-usuario/chatbot_educacao_fisica.git
cd chatbot_educacao_fisica
```

### **2. Configure as Variáveis de Ambiente**

Crie um arquivo `.env` na raiz do projeto:

```bash
# OpenAI/Anthropic
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Supabase
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Google Drive
GOOGLE_DRIVE_CREDENTIALS=path_to_credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here

# Configurações do Sistema
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### **3. Configure o Google Drive**

```bash
# 1. Acesse Google Cloud Console
# 2. Crie um projeto
# 3. Ative a Google Drive API
# 4. Crie credenciais de serviço
# 5. Baixe o arquivo JSON
# 6. Coloque em backend/token.json
```

### **4. Configure o Supabase**

```bash
# 1. Crie um projeto no Supabase
# 2. Execute as migrações SQL
# 3. Configure as políticas de segurança
# 4. Copie as chaves de API
```

## 🚀 **Deploy Rápido (Recomendado para Iniciantes)**

### **Opção 1: Render (Mais Fácil)**

1. [Fork o repositório](https://github.com/seu-usuario/chatbot_educacao_fisica/fork)
2. [Conecte ao Render](render-deployment.md#conexão-com-render)
3. [Configure as variáveis](render-deployment.md#configuração-das-variáveis)
4. [Deploy automático](render-deployment.md#deploy-automático)

### **Opção 2: Docker (Mais Profissional)**

1. [Instale o Docker](docker-deployment.md#instalação-do-docker)
2. [Configure o docker-compose](docker-deployment.md#configuração-do-docker-compose)
3. [Execute o deploy](docker-deployment.md#executando-o-deploy)

## 📊 **Comparação das Opções**

| Plataforma    | Facilidade | Custo      | Controle   | Escalabilidade | Suporte    |
| ------------- | ---------- | ---------- | ---------- | -------------- | ---------- |
| **Render**    | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐     | ⭐⭐⭐⭐       | ⭐⭐⭐⭐   |
| **Docker**    | ⭐⭐⭐     | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐     | ⭐⭐⭐     |
| **Hostinger** | ⭐⭐⭐⭐   | ⭐⭐⭐⭐   | ⭐⭐⭐⭐   | ⭐⭐⭐         | ⭐⭐⭐⭐   |
| **Local**     | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐           | ⭐⭐⭐⭐⭐ |

## 🔍 **Verificação do Deploy**

### **Checklist de Verificação:**

- [ ] Frontend acessível via HTTPS
- [ ] Backend respondendo às requisições
- [ ] Banco de dados conectado
- [ ] Autenticação funcionando
- [ ] IA respondendo corretamente
- [ ] Sincronização com Drive ativa
- [ ] Logs sem erros críticos
- [ ] Performance aceitável

### **Testes Automatizados:**

```bash
# Teste do backend
curl https://seu-backend.onrender.com/health

# Teste do frontend
curl https://seu-frontend.onrender.com

# Teste da API
curl https://seu-backend.onrender.com/api/health
```

## 🚨 **Problemas Comuns**

### **1. Erro de CORS**

```bash
# Adicione no backend
CORS_ORIGINS=["https://seu-frontend.com"]
```

### **2. Timeout de Conexão**

```bash
# Aumente no Render
TIMEOUT=300
```

### **3. Erro de Memória**

```bash
# Reduza o tamanho dos chunks
CHUNK_SIZE=1000
```

### **4. Problemas de Autenticação**

```bash
# Verifique as chaves do Supabase
# Confirme as permissões
# Teste o login localmente
```

## 📈 **Monitoramento e Manutenção**

### **Métricas Importantes:**

- **Uptime:** >99.9%
- **Response Time:** <2s
- **Error Rate:** <1%
- **Memory Usage:** <80%
- **CPU Usage:** <70%

### **Ferramentas de Monitoramento:**

- **Render:** Dashboard integrado
- **Docker:** Docker stats + Prometheus
- **Custom:** Logs + Métricas personalizadas

## 🔄 **Atualizações e Deploy Contínuo**

### **Configuração Automática:**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Render
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        uses: johnbeynon/render-deploy-action@v1.0.0
        with:
          service-id: ${{ secrets.RENDER_SERVICE_ID }}
          api-key: ${{ secrets.RENDER_API_KEY }}
```

### **Deploy Manual:**

```bash
# Atualizar código
git pull origin main

# Rebuild e restart (Docker)
docker-compose down
docker-compose up -d --build

# Rebuild e restart (Render)
# Automático via GitHub
```

## 💰 **Custos Estimados**

### **Render (Gratuito):**

- **Backend:** $0/mês (512MB RAM)
- **Frontend:** $0/mês (100GB bandwidth)
- **Banco:** $0/mês (1GB storage)

### **Hostinger:**

- **Hospedagem:** $3-10/mês
- **Domínio:** $10-15/ano
- **SSL:** Gratuito

### **Docker (VPS):**

- **VPS:** $5-20/mês
- **Domínio:** $10-15/ano
- **SSL:** Gratuito (Let's Encrypt)

## 🆘 **Suporte e Troubleshooting**

### **Recursos de Ajuda:**

- [📖 Documentação Completa](../README.md)
- [🐛 Problemas Comuns](../troubleshooting/common-issues.md)
- [🔧 Guia de Debug](../troubleshooting/debug-guide.md)
- [📞 Comunidade Discord](https://discord.gg/dnadaforca)

### **Logs Importantes:**

```bash
# Backend logs
docker logs chatbot-backend

# Frontend logs
docker logs chatbot-frontend

# Render logs
# Dashboard do Render > Logs
```

## 🎯 **Próximos Passos**

1. **Escolha sua plataforma** de deploy preferida
2. **Configure as variáveis** de ambiente
3. **Execute o deploy** seguindo o guia específico
4. **Teste o sistema** usando o checklist
5. **Configure monitoramento** para produção
6. **Documente** suas configurações específicas

---

## 📞 **Precisa de Ajuda?**

- **GitHub Issues:** [Reporte problemas](https://github.com/seu-repo/issues)
- **Discord:** [Comunidade ativa](https://discord.gg/dnadaforca)
- **Email:** suporte@dnadaforca.com

---

**📅 Última atualização:** Agosto 2025  
**🔄 Versão:** 2.0.0  
**👨‍💻 Mantido por:** Equipe DNA da Força
