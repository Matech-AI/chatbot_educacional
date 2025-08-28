# 🚀 GUIA COMPLETO DE DEPLOY - SISTEMA COMPLETO (FRONTEND + RAG + API) NO HOSTINGER VPS

## 🎯 **OBJETIVO**

Substituir **COMPLETAMENTE** o servidor Render com um sistema completo rodando no seu VPS Hostinger, baseado na configuração do `render.yaml`:

- ✅ **Frontend React** (porta 3000) - Interface do usuário
- ✅ **RAG Server** (porta 8000) - Sistema de IA e documentos
- ✅ **API Server** (porta 8001) - Autenticação e gerenciamento
- ✅ **Nginx** - Proxy reverso e balanceamento
- ✅ **Redis** - Cache e sessões
- ✅ **Sistema completo** de gerenciamento

## 📋 **INFORMAÇÕES DO SERVIDOR**

- **Provedor**: Hostinger
- **OS**: Debian 12
- **IP**: 31.97.16.142
- **Acesso**: SSH root
- **Recursos**: 200GB disco, 16TB banda

## 🔧 **ETAPA 1: CONEXÃO E PREPARAÇÃO**

### **1.1 Conectar via SSH**

```bash
ssh root@31.97.16.142
```

### **1.2 Configurar Autenticação GitHub (REPOSITÓRIO PRIVADO)**

Como o repositório é privado, você precisa configurar autenticação:

#### **A) Criar Token de Acesso Pessoal (PAT) no GitHub:**

1. **GitHub.com** → Clique no seu avatar → `Settings`
2. **Sidebar esquerda** → `Developer settings`
3. **Personal access tokens** → `Tokens (classic)`
4. **Generate new token** → `Generate new token (classic)`
5. **Note**: `Hostinger Deploy Token`
6. **Expiration**: `90 days` (ou `No expiration` para desenvolvimento)
7. **Scopes**: ✅ `repo` (Full control of private repositories)
8. **Generate token**
9. **⚠️ COPIE O TOKEN** (você não verá novamente!)

#### **B) Configurar Autenticação no Servidor:**

```bash
# 1. Configurar token e username
export GITHUB_TOKEN="SEU_TOKEN_AQUI"
export GITHUB_USERNAME="SEU_USERNAME"

# 2. Configurar Git
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@exemplo.com"

# 3. Testar conexão GitHub
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user
```

### **1.3 Executar o script de deploy COMPLETO**

```bash
# Download do script usando autenticação GitHub
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh

# Dar permissão de execução
chmod +x deploy_frontend_hostinger.sh

# Executar o deploy COMPLETO (Frontend + RAG + API)
./deploy_frontend_hostinger.sh
```

### **1.4 Sequência Completa de Comandos**

```bash
# Configurar autenticação
export GITHUB_TOKEN="SEU_TOKEN_AQUI"
export GITHUB_USERNAME="SEU_USERNAME"

# Configurar Git
git config --global user.name "Matheus"
git config --global user.email "matheusbnas@gmail.com"

# Testar conexão
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# Download e execução
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh

chmod +x deploy_frontend_hostinger.sh
./deploy_frontend_hostinger.sh
```

## ⚙️ **ETAPA 2: CONFIGURAÇÃO DAS API KEYS**

### **2.1 Editar arquivo .env**

```bash
cd /root/dna-forca-complete
nano .env
```

### **2.2 Configurar suas chaves (baseado no render.yaml)**

```bash
# ===== API KEYS =====
OPENAI_API_KEY=sk-...sua-chave-openai...
NVIDIA_API_KEY=nvapi-...sua-chave-nvidia...
GEMINI_API_KEY=...sua-chave-gemini...
GOOGLE_DRIVE_API_KEY=...sua-chave-google-drive...

# ===== CONFIGURAÇÕES JWT =====
JWT_SECRET_KEY=sua-chave-secreta-jwt-aqui
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== CONFIGURAÇÕES DE EMAIL =====
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=matheusbnas@gmail.com
EMAIL_PASSWORD=yoip qkvw aozn augl
EMAIL_FROM=matheusbnas@gmail.com
```

## 📦 **ETAPA 3: INSTALAÇÃO DAS DEPENDÊNCIAS**

### **3.1 Configurar Ambiente Virtual Python (.venv)**

```bash
# Verificar se o ambiente virtual .venv existe
ls -la .venv/

# Se não existir, criar
python3 -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate

# Verificar se está ativo
which python
pip --version
```

### **3.2 Instalar Dependências Python**

```bash
# Com o .venv ativado, instalar dependências
pip install fastapi uvicorn langchain chromadb redis

# Verificar instalação
pip list | grep -E "(fastapi|uvicorn|langchain|chromadb|redis)"
```

### **3.3 Executar script de instalação**

```bash
./install.sh
```

### **3.2 Verificar instalação**

```bash
# Verificar se o ambiente virtual foi criado
ls -la .venv/

# Verificar se as dependências Python foram instaladas
source .venv/bin/activate
pip list | grep -E "(fastapi|langchain|chromadb|redis)"

# Verificar se as dependências Node.js foram instaladas
cd frontend
ls -la node_modules/
cd ..
```

## 🏗️ **ETAPA 4: BUILD DO FRONTEND**

### **4.1 Fazer build do frontend**

```bash
./build_frontend.sh
```

### **4.2 Verificar build**

```bash
# Verificar se o build foi criado
ls -la frontend/dist/

# Verificar tamanho do build
du -sh frontend/dist/
```

## 🚀 **ETAPA 5: INICIALIZAÇÃO DO SISTEMA COMPLETO**

### **5.1 Primeira execução**

```bash
./start_all.sh
```

### **5.2 Verificar se está funcionando**

```bash
# Em outro terminal SSH
curl http://localhost:3000          # Frontend
curl http://localhost:8000/status   # RAG Server
curl http://localhost:8001/status   # API Server
curl http://localhost/health        # Nginx Health Check
```

## 🌐 **ETAPA 6: CONFIGURAÇÃO DO NGINX E FIREWALL**

### **6.1 Verificar configuração do Nginx**

```bash
nginx -t
```

### **6.2 Reiniciar Nginx**

```bash
systemctl restart nginx
systemctl enable nginx
```

### **6.3 Configurar firewall**

```bash
ufw allow 80      # Nginx
ufw allow 3000    # Frontend
ufw allow 8000    # RAG Server
ufw allow 8001    # API Server
ufw enable
```

## 📊 **ETAPA 7: MONITORAMENTO E MANUTENÇÃO**

### **7.1 Verificar status completo**

```bash
./status.sh
```

### **7.2 Monitoramento em tempo real**

```bash
./monitor.sh
```

### **7.3 Ver logs específicos**

```bash
# Frontend
tail -f logs/frontend.log

# RAG Server
tail -f logs/rag-server.log

# API Server
tail -f logs/api-server.log

# Todos os logs
tail -f logs/*.log
```

## 🔄 **ETAPA 8: UPLOAD DE MATERIAIS E DADOS**

### **8.1 Estratégia de Deploy**

O sistema usa uma estratégia de **deploy em duas etapas**:

1. **Deploy base** - Clona repositório e configura sistema
2. **Upload de materiais** - Sobe arquivos grandes depois

### **8.2 Copiar arquivos do projeto local**

```bash
# No seu computador local
# Copiar materiais para o servidor
scp -r data/materials/* root@31.97.16.142:/root/dna-forca-complete/data/materials/

# Copiar ChromaDB para o servidor
scp -r backend/data/.chromadb/* root@31.97.16.142:/root/dna-forca-complete/backend/data/.chromadb/
```

### **8.3 Upload automático para GitHub**

```bash
# No servidor da Hostinger
cd /root/dna-forca-complete

# Executar script de upload
./upload_materials.sh

# Fazer upload manual
git add data/
git commit -m "Adicionar materiais e dados do projeto local"
git push origin main
```

### **8.4 Verificar upload**

```bash
# Verificar se os arquivos foram adicionados
git status

# Ver tamanho dos diretórios
du -sh data/materials/
du -sh data/.chromadb/

# Ver arquivos no GitHub
git ls-files | grep -E "data/|chromadb"
```

## 👨‍💼 **ETAPA 9: DEPLOY AUTOMÁTICO (OPCIONAL)**

### **9.1 Configurar Supervisor**

```bash
# O script já criou a configuração
systemctl restart supervisor
systemctl enable supervisor
```

### **9.2 Verificar processos**

```bash
supervisorctl status
supervisorctl restart frontend
supervisorctl restart rag-server
supervisorctl restart api-server
```

## 📁 **ESTRUTURA FINAL DO PROJETO**

```
/root/dna-forca-complete/
├── .env                          # Configurações e API keys
├── start_all.sh                  # Script de inicialização completa
├── stop_all.sh                   # Script de parada completa
├── status.sh                     # Script de status
├── restart.sh                    # Script de reinicialização
├── install.sh                    # Script de instalação
├── build_frontend.sh             # Script de build do frontend
├── monitor.sh                    # Script de monitoramento
├── backup.sh                     # Script de backup
├── cleanup.sh                    # Script de limpeza
├── upload_materials.sh           # Script de upload de materiais
├── .venv/                        # Ambiente virtual Python
├── frontend/                     # Sistema Frontend
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── start.sh
│   ├── build.sh
│   ├── node_modules/             # Dependências Node.js
│   └── dist/                     # Build de produção
├── rag_server/                   # Sistema RAG
│   ├── requirements.txt
│   ├── start.sh
│   └── [arquivos do RAG]
├── api_server/                   # Sistema API
│   ├── requirements.txt
│   ├── start.sh
│   └── [arquivos da API]
├── shared/                       # Dependências compartilhadas
│   └── requirements.txt
├── data/                         # Dados do sistema
│   ├── materials/                # Materiais para processar
│   └── .chromadb/               # Banco de dados vetorial
├── logs/                         # Logs do sistema
│   ├── frontend.log
│   ├── rag-server.log
│   ├── api-server.log
│   ├── frontend.pid
│   ├── rag-server.pid
│   └── api-server.pid
└── backups/                      # Backups automáticos
```

## 📤 **SCRIPT DE UPLOAD AUTOMÁTICO**

### **Funcionalidades do upload_materials.sh:**

- ✅ **Verificação automática** de arquivos
- ✅ **Contagem de arquivos** e tamanho
- ✅ **Instruções passo a passo** para upload
- ✅ **Suporte a Git LFS** para arquivos grandes
- ✅ **Validação** de repositório git

### **Uso do script:**

```bash
# Verificar arquivos disponíveis
./upload_materials.sh

# Upload automático (se implementado)
./upload_materials.sh --auto

# Ver ajuda
./upload_materials.sh --help
```

## 🚀 **ESTRATÉGIA COMPLETA DE DEPLOY**

### **Fase 1: Deploy Base**

1. ✅ Clonar repositório GitHub
2. ✅ Instalar dependências
3. ✅ Configurar ambiente
4. ✅ Build do frontend
5. ✅ Sistema funcionando

### **Fase 2: Upload de Materiais**

1. 📁 Copiar arquivos do projeto local
2. 📤 Fazer upload para GitHub
3. 📤 Sincronizar repositório
4. 📤 Sistema completo com dados

### **Vantagens desta abordagem:**

- 🚀 **Deploy rápido** - Sistema funcionando em minutos
- 📁 **Flexibilidade** - Escolhe o que subir
- 💾 **Controle de tamanho** - Gerencia arquivos grandes
- 🔄 **Sincronização** - Mantém GitHub atualizado

## 🌐 **URLS DE ACESSO**

### **Acesso Direto:**

- **Frontend**: http://31.97.16.142:3000
- **RAG Server**: http://31.97.16.142:8000
- **API Server**: http://31.97.16.142:8001

### **Acesso via Nginx (Recomendado):**

- **Frontend**: http://31.97.16.142 (página principal)
- **RAG Server**: http://31.97.16.142/rag/
- **API Server**: http://31.97.16.142/api/
- **Documentação RAG**: http://31.97.16.142/rag/docs
- **Documentação API**: http://31.97.16.142/api/docs
- **Health Check**: http://31.97.16.142/health

## 🔧 **COMANDOS ÚTEIS**

### **🔐 Autenticação GitHub (Repositório Privado)**

```bash
# Configurar token (SUBSTITUA SEU_TOKEN_AQUI)
export GITHUB_TOKEN="SEU_TOKEN_AQUI"
export GITHUB_USERNAME="SEU_USERNAME"

# Testar conexão GitHub
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# Download do script com autenticação
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh

# Verificar download
ls -la deploy_frontend_hostinger.sh
head -5 deploy_frontend_hostinger.sh
```

### **🚀 Deploy Rápido (Com Token Configurado)**

```bash
# Deploy completo em um comando
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh && \
chmod +x deploy_frontend_hostinger.sh && \
./deploy_frontend_hostinger.sh
```

### **Gerenciamento do Sistema**

```bash
# Iniciar sistema completo
./start_all.sh

# Parar sistema completo
./stop_all.sh

# Verificar status
./status.sh

# Reinicializar sistema
./restart.sh

# Monitoramento
./monitor.sh
```

### **Upload de Materiais:**

```bash
# Verificar arquivos disponíveis
./upload_materials.sh

# Fazer upload para GitHub
git add data/
git commit -m "Adicionar materiais e dados"
git push origin main

# Verificar status do git
git status
git ls-files | grep -E "data/|materials"
```

### **Gerenciamento do Frontend**

```bash
# Build do frontend
./build_frontend.sh

# Iniciar apenas frontend
cd frontend && ./start.sh

# Ver logs do frontend
tail -f logs/frontend.log
```

### **Gerenciamento Individual**

```bash
# Iniciar apenas RAG Server
cd rag_server && ./start.sh

# Iniciar apenas API Server
cd api_server && ./start.sh

# Ver logs específicos
tail -f logs/rag-server.log
tail -f logs/api-server.log
```

### **Gerenciamento de Dados**

```bash
# Fazer backup
./backup.sh

# Limpeza automática
./cleanup.sh

# Verificar uso de disco
df -h /root/dna-forca-complete/data/
```

## 🚨 **TROUBLESHOOTING**

### **Problema: Frontend não inicia**

```bash
# Verificar logs
tail -f logs/frontend.log

# Verificar se o build existe
ls -la frontend/dist/

# Fazer build novamente
./build_frontend.sh

# Verificar dependências Node.js
cd frontend && npm list
```

### **Problema: Sistema não inicia**

```bash
# Verificar logs
tail -f logs/*.log

# Verificar variáveis de ambiente
cat .env

# Verificar dependências
source .venv/bin/activate
pip list
```

### **Problema: Porta já em uso**

```bash
# Verificar o que está usando as portas
netstat -tlnp | grep -E ":3000|:8000|:8001"

# Matar processos
pkill -f "vite.*preview"
pkill -f "uvicorn.*rag_server"
pkill -f "uvicorn.*api_server"
```

### **Problema: Nginx não funciona**

```bash
# Verificar configuração
nginx -t

# Verificar status
systemctl status nginx

# Ver logs do Nginx
tail -f /var/log/nginx/error.log
```

### **Problema: Build do frontend falha**

```bash
# Verificar versão do Node.js
node --version
npm --version

# Limpar cache
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### **Problema: Erro 404 ao baixar script (Repositório Privado)**

```bash
# ❌ ERRO: 404: Not Found
# ✅ SOLUÇÃO: Configurar autenticação GitHub

# 1. Verificar se o token está configurado
echo $GITHUB_TOKEN

# 2. Testar conexão com GitHub
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# 3. Verificar acesso ao repositório
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/Matech-AI/chatbot_educacional

# 4. Download correto com autenticação
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh

# 5. Verificar se o download funcionou
ls -la deploy_frontend_hostinger.sh
head -5 deploy_frontend_hostinger.sh
```

### **Problema: Token GitHub expirado ou inválido**

```bash
# ❌ ERRO: Bad credentials
# ✅ SOLUÇÃO: Renovar token

# 1. Criar novo token no GitHub
# GitHub.com → Settings → Developer settings → Personal access tokens

# 2. Configurar novo token
export GITHUB_TOKEN="NOVO_TOKEN_AQUI"

# 3. Testar novo token
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# 4. Fazer download novamente
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh
```

### **Problema: Permissões insuficientes no token**

```bash
# ❌ ERRO: Not found (mesmo com token)
# ✅ SOLUÇÃO: Verificar permissões

# 1. Verificar scopes do token
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# 2. Token deve ter permissão 'repo' (Full control of private repositories)
# 3. Se não tiver, criar novo token com permissões corretas
```

## 🚨 **TROUBLESHOOTING DE UPLOAD**

### **Problema: Arquivos muito grandes**

```bash
# Configurar Git LFS
git lfs install
git lfs track "data/**"
git lfs track "*.pdf"
git lfs track "*.docx"

# Adicionar .gitattributes
git add .gitattributes
git commit -m "Configurar Git LFS"
git push origin main
```

### **Problema: Falha no push**

```bash
# Verificar tamanho do repositório
git count-objects -vH

# Limpar histórico se necessário
git gc --aggressive
git prune

# Forçar push
git push origin main --force
```

### **Problema: Arquivos não aparecem**

```bash
# Verificar se foram adicionados
git status
git ls-files | grep -E "data/|materials"

# Verificar se estão no .gitignore
cat .gitignore | grep -i "data\|materials"

# Adicionar manualmente
git add -f data/materials/
git add -f data/.chromadb/
```

## 📈 **OTIMIZAÇÕES RECOMENDADAS**

### **1. Configuração do Frontend**

```bash
# Otimizar build do Vite
cd frontend
nano vite.config.ts

# Adicionar otimizações
build: {
  outDir: 'dist',
  sourcemap: false,
  minify: 'terser',
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom'],
        router: ['react-router-dom']
      }
    }
  }
}
```

### **2. Configuração do Uvicorn**

```bash
# Editar start.sh para usar mais workers
uvicorn rag_server:app --host 0.0.0.0 --port 8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### **3. Configuração do Nginx**

```bash
# Otimizar Nginx para produção
nano /etc/nginx/nginx.conf

# Aumentar workers
worker_processes auto;
worker_connections 1024;

# Adicionar gzip
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

## 🔒 **SEGURANÇA**

### **1. Segurança de Tokens GitHub**

#### **A) Boas Práticas para Tokens:**

```bash
# ✅ RECOMENDADO:
# - Usar expiração de 90 dias para produção
# - Usar permissões mínimas necessárias (apenas 'repo')
# - Nunca compartilhar tokens em logs ou código
# - Revogar tokens não utilizados

# ❌ NUNCA FAZER:
# - Usar tokens sem expiração em produção
# - Dar permissões excessivas (admin, delete_repo, etc.)
# - Compartilhar tokens em mensagens ou commits
# - Usar tokens pessoais em CI/CD público
```

#### **B) Gerenciamento de Tokens:**

```bash
# 1. Listar tokens ativos
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/authorizations

# 2. Revogar token específico (se necessário)
curl -X DELETE \
     -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/authorizations/TOKEN_ID

# 3. Verificar permissões do token atual
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user
```

#### **C) Configuração Segura no Servidor:**

```bash
# 1. Usar variáveis de ambiente (não hardcoded)
export GITHUB_TOKEN="SEU_TOKEN_AQUI"

# 2. Configurar no .bashrc para persistência
echo 'export GITHUB_TOKEN="SEU_TOKEN_AQUI"' >> ~/.bashrc
source ~/.bashrc

# 3. Verificar se está configurado
echo $GITHUB_TOKEN

# 4. Limpar histórico de comandos (opcional)
history -c
```

### **2. Firewall Completo**

```bash
# Configurar firewall restritivo
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 3000
ufw allow 8000
ufw allow 8001
ufw enable
```

### **2. Usuário não-root (Recomendado)**

```bash
# Criar usuário específico
adduser dnaforca
usermod -aG sudo dnaforca

# Transferir projeto
cp -r /root/dna-forca-complete /home/dnaforca/
chown -R dnaforca:dnaforca /home/dnaforca/dna-forca-complete
```

### **3. SSL/HTTPS (Recomendado para produção)**

```bash
# Instalar Certbot
apt install certbot python3-certbot-nginx

# Gerar certificado
certbot --nginx -d seu-dominio.com
```

## 📞 **SUPORTE**

### **Logs importantes**

- **Frontend**: `/root/dna-forca-complete/logs/frontend.log`
- **RAG Server**: `/root/dna-forca-complete/logs/rag-server.log`
- **API Server**: `/root/dna-forca-complete/logs/api-server.log`
- **Nginx**: `/var/log/nginx/`
- **Redis**: `/var/log/redis/`
- **Sistema**: `/var/log/syslog`

### **Comandos de diagnóstico**

```bash
# Status completo do sistema
./status.sh

# Monitoramento em tempo real
./monitor.sh

# Verificar conectividade
ping google.com
curl -I http://localhost:3000
curl -I http://localhost:8000
curl -I http://localhost:8001

# Verificar recursos
free -h
df -h
top
```

## ✅ **CHECKLIST DE DEPLOY COMPLETO**

### **🔐 Autenticação GitHub (Repositório Privado)**

- [ ] Token de acesso pessoal criado no GitHub
- [ ] Token com permissão 'repo' (Full control of private repositories)
- [ ] Token configurado no servidor via `export GITHUB_TOKEN`
- [ ] Conexão GitHub testada com `curl -H "Authorization: token $GITHUB_TOKEN"`
- [ ] Script `deploy_frontend_hostinger.sh` baixado com sucesso

### **🚀 Deploy do Sistema**

- [ ] Script de deploy executado
- [ ] API keys configuradas no .env
- [ ] Dependências Python instaladas
- [ ] Dependências Node.js instaladas
- [ ] Frontend buildado com sucesso
- [ ] Sistema completo iniciado e funcionando
- [ ] Nginx configurado e funcionando
- [ ] Redis configurado e funcionando
- [ ] Firewall configurado
- [ ] Backup configurado
- [ ] Monitoramento funcionando
- [ ] Logs sendo gerados
- [ ] Acesso externo funcionando
- [ ] Proxy reverso funcionando
- [ ] Health checks funcionando
- [ ] Frontend acessível via Nginx

### **📤 Upload de Materiais:**

- [ ] Arquivos copiados do projeto local
- [ ] Script upload_materials.sh executado
- [ ] Arquivos adicionados ao git
- [ ] Commit realizado
- [ ] Push para GitHub
- [ ] Verificação no GitHub
- [ ] Sistema funcionando com dados

## 🎯 **PRÓXIMOS PASSOS**

1. **Testar frontend** acessando http://31.97.16.142
2. **Testar APIs** com perguntas simples
3. **Copiar materiais** do projeto local para o servidor
4. **Executar upload_materials.sh** para subir arquivos
5. **Fazer upload de materiais** via endpoint `/rag/process-materials`
6. **Configurar backup automático** via cron
7. **Implementar monitoramento** mais avançado
8. **Configurar domínio** personalizado (opcional)
9. **Configurar SSL/HTTPS** para produção
10. **Implementar rate limiting** no Nginx
11. **Configurar alertas** de monitoramento

## 🔄 **MIGRAÇÃO DO RENDER**

### **1. Atualizar configurações do frontend**

```javascript
// O frontend já está configurado para usar as URLs locais
// via proxy no vite.config.ts
const API_BASE = "/api"; // Proxy para localhost:8001
const RAG_API_BASE = "/rag-api"; // Proxy para localhost:8000
```

### **2. Testar funcionalidades**

- ✅ Interface do usuário (React)
- ✅ Chat educacional
- ✅ Upload de materiais
- ✅ Processamento RAG
- ✅ Autenticação
- ✅ Gerenciamento de usuários

### **3. Desativar Render**

- Parar serviços no Render
- Redirecionar tráfego para seu VPS
- Monitorar performance

---

## 🎉 **PARABÉNS! SISTEMA COMPLETO FUNCIONANDO!**

**🎯 Você agora tem um sistema COMPLETO (3 SERVIDORES) rodando no seu VPS Hostinger que substitui 100% o Render!**

### **✅ VANTAGENS DO SEU VPS:**

- **Controle total** sobre a infraestrutura
- **Custo reduzido** (sem taxas do Render)
- **Performance dedicada** (200GB disco, 16TB banda)
- **Segurança personalizada** (firewall, SSL)
- **Backup automático** e monitoramento
- **Escalabilidade** conforme necessário
- **Frontend otimizado** com build de produção

### **📋 PARA DÚVIDAS OU PROBLEMAS:**

1. Verifique os logs: `./monitor.sh`
2. Use os scripts de diagnóstico: `./status.sh`
3. Consulte o troubleshooting acima
4. Verifique a documentação das APIs
5. Use o script de build: `./build_frontend.sh`

**🚀 Seu sistema DNA da Força está rodando independentemente do Render com FRONTEND + RAG + API!**

### **🎨 FRONTEND ESPECIALMENTE:**

- **Build otimizado** para produção
- **Proxy automático** para APIs
- **Tailwind CSS** configurado
- **TypeScript** configurado
- **Vite** para desenvolvimento rápido
- **Nginx** servindo arquivos estáticos
- **Hot reload** em desenvolvimento
