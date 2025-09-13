# 🌐 GUIA COMPLETO - REGISTRO DO DOMÍNIO aidnadaforca.com.br NA HOSTINGER

## 🎯 **OBJETIVO**

Registrar o domínio `aidnadaforca.com.br` na Hostinger e configurar para apontar para o servidor VPS `31.97.16.142` onde está rodando o sistema completo.

## 📋 **INFORMAÇÕES NECESSÁRIAS**

- **Domínio**: `aidnadaforca.com.br`
- **Servidor VPS**: `31.97.16.142`
- **Conta Hostinger**: `root@31.97.16.142`
- **Sistema**: Frontend + RAG + API rodando

## 🔧 **ETAPA 1: VERIFICAR DISPONIBILIDADE DO DOMÍNIO**

### **1.1 Verificar se o domínio está disponível**

```bash
# No servidor VPS (opcional - verificação local)
nslookup aidnadaforca.com.br
dig aidnadaforca.com.br
```

### **1.2 Verificar no painel da Hostinger**

1. **Acesse**: https://www.hostinger.com.br
2. **Faça login** na sua conta
3. **Vá para**: Domínios → Registrar Domínio
4. **Digite**: `aidnadaforca.com.br`
5. **Verifique disponibilidade**

## 🛒 **ETAPA 2: REGISTRAR O DOMÍNIO**

### **2.1 Processo de Registro**

1. **Selecione o domínio** `aidnadaforca.com.br`
2. **Escolha o período** (1 ano recomendado)
3. **Adicione proteção de privacidade** (recomendado)
4. **Configure DNS automático** (será ajustado depois)
5. **Finalize a compra**

### **2.2 Configurações Recomendadas**

- **Período**: 1 ano (renovação automática)
- **Proteção de privacidade**: ✅ Ativada
- **DNS automático**: ✅ Ativado (ajustaremos depois)
- **Auto-renovação**: ✅ Ativada

## ⚙️ **ETAPA 3: CONFIGURAR DNS**

### **3.1 Acessar Painel de DNS**

1. **Hostinger** → **Domínios** → **Gerenciar**
2. **Selecione** `aidnadaforca.com.br`
3. **Vá para** **Zona DNS** ou **DNS**

### **3.2 Configurar Registros DNS**

#### **A) Registro A (Principal)**

```
Tipo: A
Nome: @
Valor: 31.97.16.142
TTL: 3600
```

#### **B) Registro A (www)**

```
Tipo: A
Nome: www
Valor: 31.97.16.142
TTL: 3600
```

#### **C) Registro CNAME (api - opcional)**

```
Tipo: CNAME
Nome: api
Valor: aidnadaforca.com.br
TTL: 3600
```

#### **D) Registro CNAME (rag - opcional)**

```
Tipo: CNAME
Nome: rag
Valor: aidnadaforca.com.br
TTL: 3600
```

### **3.3 Configuração Completa DNS**

```
# Registros obrigatórios
@           A       31.97.16.142    3600
www         A       31.97.16.142    3600

# Registros opcionais (subdomínios)
api         CNAME   aidnadaforca.com.br    3600
rag         CNAME   aidnadaforca.com.br    3600
admin       CNAME   aidnadaforca.com.br    3600

# Registros de email (se necessário)
@           MX      mail.aidnadaforca.com.br    3600
mail        A       31.97.16.142    3600
```

## 🔧 **ETAPA 4: CONFIGURAR NGINX NO SERVIDOR**

### **4.1 Criar configuração do domínio**

```bash
# Conectar no servidor VPS
ssh root@31.97.16.142

# Criar configuração do domínio
nano /etc/nginx/sites-available/aidnadaforca.com.br
```

### **4.2 Configuração Nginx para o domínio**

```nginx
server {
    listen 80;
    server_name aidnadaforca.com.br www.aidnadaforca.com.br;

    # Redirecionar www para não-www
    if ($host = www.aidnadaforca.com.br) {
        return 301 http://aidnadaforca.com.br$request_uri;
    }

    # Frontend (React)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API Server
    location /api/ {
        proxy_pass http://localhost:8001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # RAG Server
    location /rag/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8001/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Logs
    access_log /var/log/nginx/aidnadaforca.com.br.access.log;
    error_log /var/log/nginx/aidnadaforca.com.br.error.log;
}
```

### **4.3 Ativar configuração do domínio**

```bash
# Criar link simbólico
ln -s /etc/nginx/sites-available/aidnadaforca.com.br /etc/nginx/sites-enabled/

# Testar configuração
nginx -t

# Recarregar Nginx
systemctl reload nginx
systemctl restart nginx
```

## 🔒 **ETAPA 5: CONFIGURAR SSL/HTTPS (RECOMENDADO)**

### **5.1 Instalar Certbot**

```bash
# Instalar Certbot
apt update
apt install certbot python3-certbot-nginx

# Gerar certificado SSL
certbot --nginx -d aidnadaforca.com.br -d www.aidnadaforca.com.br
```

### **5.2 Configuração automática SSL**

O Certbot irá:

1. **Gerar certificado** Let's Encrypt
2. **Configurar HTTPS** automaticamente
3. **Configurar redirecionamento** HTTP → HTTPS
4. **Configurar renovação automática**

### **5.3 Verificar SSL**

```bash
# Verificar certificado
certbot certificates

# Testar renovação
certbot renew --dry-run

# Verificar status
systemctl status certbot.timer
```

## 🌐 **ETAPA 6: CONFIGURAR FIREWALL**

### **6.1 Configurar UFW**

```bash
# Permitir tráfego HTTP e HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Verificar status
ufw status

# Se necessário, permitir SSH
ufw allow ssh
ufw allow 22/tcp
```

### **6.2 Verificar portas abertas**

```bash
# Verificar portas abertas
netstat -tlnp | grep -E ":80|:443|:3000|:8000|:8001"

# Verificar se Nginx está escutando
ss -tlnp | grep nginx
```

## 🧪 **ETAPA 7: TESTAR CONFIGURAÇÃO**

### **7.1 Testes locais no servidor**

```bash
# Testar localmente
curl -I http://localhost
curl -I http://aidnadaforca.com.br
curl -I http://www.aidnadaforca.com.br

# Testar APIs
curl -I http://localhost/api/status
curl -I http://localhost/rag/status
```

### **7.2 Testes externos**

```bash
# Testar DNS (aguardar propagação - até 24h)
nslookup aidnadaforca.com.br
dig aidnadaforca.com.br

# Testar conectividade
ping aidnadaforca.com.br
curl -I http://aidnadaforca.com.br
curl -I https://aidnadaforca.com.br
```

### **7.3 Verificar propagação DNS**

```bash
# Usar ferramentas online
# https://www.whatsmydns.net/
# https://dnschecker.org/

# Ou via comando
dig @8.8.8.8 aidnadaforca.com.br
dig @1.1.1.1 aidnadaforca.com.br
```

## 📱 **ETAPA 8: CONFIGURAR FRONTEND PARA O DOMÍNIO**

### **8.1 Atualizar configurações do frontend**

```bash
# No servidor VPS
cd /root/dna-forca-complete

# Editar vite.config.ts
nano vite.config.ts
```

### **8.2 Configuração Vite para produção**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true,
        secure: false,
      },
      "/rag": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
    minify: "terser",
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          router: ["react-router-dom"],
        },
      },
    },
  },
  base: "/",
});
```

### **8.3 Rebuild do frontend**

```bash
# Fazer build para produção
npm run build

# Verificar se o build foi criado
ls -la dist/

# Reiniciar sistema
./restart.sh
```

## 🔄 **ETAPA 9: CONFIGURAR RENOVAÇÃO AUTOMÁTICA SSL**

### **9.1 Verificar renovação automática**

```bash
# Verificar se o timer está ativo
systemctl status certbot.timer

# Verificar próximas execuções
systemctl list-timers | grep certbot

# Testar renovação manual
certbot renew --dry-run
```

### **9.2 Configurar log de renovação**

```bash
# Adicionar ao crontab (opcional)
crontab -e

# Adicionar linha:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 **ETAPA 10: MONITORAMENTO E LOGS**

### **10.1 Configurar logs específicos do domínio**

```bash
# Ver logs do domínio
tail -f /var/log/nginx/aidnadaforca.com.br.access.log
tail -f /var/log/nginx/aidnadaforca.com.br.error.log

# Ver logs do sistema
tail -f /root/dna-forca-complete/logs/*.log
```

### **10.2 Monitoramento de uptime**

```bash
# Script de monitoramento
nano /root/monitor_domain.sh
```

```bash
#!/bin/bash
# Monitoramento do domínio

DOMAIN="aidnadaforca.com.br"
LOG_FILE="/root/domain_monitor.log"

echo "$(date): Verificando $DOMAIN" >> $LOG_FILE

# Testar HTTP
if curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN | grep -q "200"; then
    echo "$(date): HTTP OK" >> $LOG_FILE
else
    echo "$(date): HTTP FALHOU" >> $LOG_FILE
fi

# Testar HTTPS
if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN | grep -q "200"; then
    echo "$(date): HTTPS OK" >> $LOG_FILE
else
    echo "$(date): HTTPS FALHOU" >> $LOG_FILE
fi

# Testar API
if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/api/status | grep -q "200"; then
    echo "$(date): API OK" >> $LOG_FILE
else
    echo "$(date): API FALHOU" >> $LOG_FILE
fi
```

```bash
# Dar permissão de execução
chmod +x /root/monitor_domain.sh

# Executar monitoramento
/root/monitor_domain.sh
```

## 🎯 **ETAPA 11: CONFIGURAÇÕES FINAIS**

### **11.1 Atualizar scripts do sistema**

```bash
# Atualizar start_all.sh para incluir verificação do domínio
nano /root/dna-forca-complete/start_all.sh
```

### **11.2 Adicionar verificação de domínio**

```bash
#!/bin/bash
# Script de inicialização com verificação de domínio

echo "🚀 Iniciando sistema DNA da Força..."

# Verificar se o domínio está configurado
if nslookup aidnadaforca.com.br > /dev/null 2>&1; then
    echo "✅ Domínio aidnadaforca.com.br configurado"
else
    echo "⚠️ Domínio aidnadaforca.com.br não encontrado"
fi

# Iniciar serviços
echo "🔄 Iniciando serviços..."

# Frontend
echo "🌐 Iniciando Frontend..."
cd /root/dna-forca-complete
npm run preview -- --host 0.0.0.0 --port 3000 > logs/frontend.log 2>&1 &
echo $! > logs/frontend.pid

# RAG Server
echo "🤖 Iniciando RAG Server..."
cd /root/dna-forca-complete/backend/rag_system
source /root/dna-forca-complete/.venv/bin/activate
uvicorn rag_handler:app --host 0.0.0.0 --port 8000 > /root/dna-forca-complete/logs/rag-server.log 2>&1 &
echo $! > /root/dna-forca-complete/logs/rag-server.pid

# API Server
echo "🔧 Iniciando API Server..."
cd /root/dna-forca-complete/backend
source /root/dna-forca-complete/.venv/bin/activate
uvicorn api_server:app --host 0.0.0.0 --port 8001 > /root/dna-forca-complete/logs/api-server.log 2>&1 &
echo $! > /root/dna-forca-complete/logs/api-server.pid

echo "✅ Sistema iniciado!"
echo "🌐 Acesse: https://aidnadaforca.com.br"
echo "🔧 API: https://aidnadaforca.com.br/api/docs"
echo "🤖 RAG: https://aidnadaforca.com.br/rag/docs"
```

### **11.3 Testar sistema completo**

```bash
# Executar script atualizado
./start_all.sh

# Verificar status
./status.sh

# Testar URLs
curl -I https://aidnadaforca.com.br
curl -I https://aidnadaforca.com.br/api/status
curl -I https://aidnadaforca.com.br/rag/status
```

## 📋 **CHECKLIST FINAL**

### **✅ Registro do Domínio**

- [ ] Domínio `aidnadaforca.com.br` registrado na Hostinger
- [ ] Proteção de privacidade ativada
- [ ] Auto-renovação configurada

### **✅ Configuração DNS**

- [ ] Registro A (@) apontando para 31.97.16.142
- [ ] Registro A (www) apontando para 31.97.16.142
- [ ] TTL configurado para 3600
- [ ] Propagação DNS verificada

### **✅ Configuração Nginx**

- [ ] Site configurado em `/etc/nginx/sites-available/aidnadaforca.com.br`
- [ ] Link simbólico criado em `/etc/nginx/sites-enabled/`
- [ ] Configuração testada com `nginx -t`
- [ ] Nginx reiniciado

### **✅ SSL/HTTPS**

- [ ] Certbot instalado
- [ ] Certificado SSL gerado
- [ ] HTTPS configurado
- [ ] Redirecionamento HTTP → HTTPS ativo
- [ ] Renovação automática configurada

### **✅ Firewall**

- [ ] Portas 80 e 443 abertas
- [ ] UFW configurado
- [ ] Conectividade testada

### **✅ Sistema**

- [ ] Frontend acessível via domínio
- [ ] API acessível via domínio
- [ ] RAG acessível via domínio
- [ ] Logs configurados
- [ ] Monitoramento ativo

## 🌐 **URLs FINAIS**

Após a configuração completa, o sistema estará acessível em:

- **Frontend**: https://aidnadaforca.com.br
- **API**: https://aidnadaforca.com.br/api/
- **RAG**: https://aidnadaforca.com.br/rag/
- **Documentação API**: https://aidnadaforca.com.br/api/docs
- **Documentação RAG**: https://aidnadaforca.com.br/rag/docs
- **Health Check**: https://aidnadaforca.com.br/health

## 🚨 **TROUBLESHOOTING**

### **Problema: Domínio não resolve**

```bash
# Verificar DNS
nslookup aidnadaforca.com.br
dig aidnadaforca.com.br

# Aguardar propagação (até 24h)
# Usar ferramentas online: whatsmydns.net
```

### **Problema: SSL não funciona**

```bash
# Verificar certificado
certbot certificates

# Renovar certificado
certbot renew --force-renewal

# Verificar configuração Nginx
nginx -t
```

### **Problema: Site não carrega**

```bash
# Verificar se os serviços estão rodando
./status.sh

# Verificar logs
tail -f logs/*.log

# Verificar Nginx
systemctl status nginx
tail -f /var/log/nginx/error.log
```

## 🎉 **SISTEMA COMPLETO COM DOMÍNIO!**

Após seguir todos os passos, você terá:

- ✅ **Domínio registrado** e configurado
- ✅ **SSL/HTTPS** funcionando
- ✅ **Sistema completo** acessível via domínio
- ✅ **Monitoramento** e logs configurados
- ✅ **Renovação automática** SSL
- ✅ **Firewall** configurado

**🚀 Seu sistema DNA da Força estará acessível em https://aidnadaforca.com.br!**
