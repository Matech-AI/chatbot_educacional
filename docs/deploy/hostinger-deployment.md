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

### **1.2 Executar o script de deploy COMPLETO**

```bash
# Baixar o script
wget https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh

# Dar permissão de execução
chmod +x deploy_frontend_hostinger.sh

# Executar o deploy COMPLETO (Frontend + RAG + API)
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

### **3.1 Executar script de instalação**

```bash
./install.sh
```

### **3.2 Verificar instalação**

```bash
# Verificar se o ambiente virtual foi criado
ls -la venv/

# Verificar se as dependências Python foram instaladas
source venv/bin/activate
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

## 🔄 **ETAPA 8: DEPLOY AUTOMÁTICO (OPCIONAL)**

### **8.1 Configurar Supervisor**

```bash
# O script já criou a configuração
systemctl restart supervisor
systemctl enable supervisor
```

### **8.2 Verificar processos**

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
├── venv/                         # Ambiente virtual Python
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
source venv/bin/activate
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

### **1. Firewall Completo**

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

## 🎯 **PRÓXIMOS PASSOS**

1. **Testar frontend** acessando http://31.97.16.142
2. **Testar APIs** com perguntas simples
3. **Fazer upload de materiais** via endpoint `/rag/process-materials`
4. **Configurar backup automático** via cron
5. **Implementar monitoramento** mais avançado
6. **Configurar domínio** personalizado (opcional)
7. **Configurar SSL/HTTPS** para produção
8. **Implementar rate limiting** no Nginx
9. **Configurar alertas** de monitoramento

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
