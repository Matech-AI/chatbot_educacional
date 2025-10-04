# 🔥 Guia de Configuração do Firewall - Hostinger

## 📋 **Visão Geral**

Este guia explica como configurar o firewall da Hostinger para permitir acesso externo ao sistema DNA da Força.

## 🚨 **Problema Identificado**

- **Servidor**: Hostinger VPS
- **IP Público**: 179.157.157.190
- **Portas bloqueadas**: 3000, 5000, 5001
- **Sintoma**: Conectividade OK (ping funciona), mas portas não respondem

## 🛠️ **Solução: Abrir Portas no Firewall**

### **Portas Necessárias:**

| Serviço    | Porta | Protocolo | Descrição                  |
| ---------- | ----- | --------- | -------------------------- |
| Frontend   | 3000  | TCP       | Interface React do usuário |
| RAG Server | 5000  | TCP       | Servidor de IA/RAG         |
| API Server | 5001  | TCP       | API REST do sistema        |

## 📱 **Passo a Passo - Painel da Hostinger**

### **1. Acesso ao Painel**

- URL: https://www.hostinger.com.br/
- Login com suas credenciais
- Navegar para seção **"VPS"** ou **"Servidores"**

### **2. Localizar Configurações de Firewall**

Procurar por uma destas opções:

- **"Firewall"**
- **"Segurança"**
- **"Configurações de rede"**
- **"Regras de firewall"**
- **"Portas"**

### **3. Criar Regras de Entrada (INBOUND)**

#### **Regra 1 - Frontend (Porta 3000)**

```
Protocolo: TCP
Porta: 3000
Ação: PERMITIR
Origem: 0.0.0.0/0 (todas as origens)
Descrição: Frontend React - DNA da Força
```

#### **Regra 2 - RAG Server (Porta 5000)**

```
Protocolo: TCP
Porta: 5000
Ação: PERMITIR
Origem: 0.0.0.0/0 (todas as origens)
Descrição: RAG Server - IA/Processamento
```

#### **Regra 3 - API Server (Porta 5001)**

```
Protocolo: TCP
Porta: 5001
Ação: PERMITIR
Origem: 0.0.0.0/0 (todas as origens)
Descrição: API Server - Backend REST
```

### **4. Aplicar Configurações**

- Clicar em **"Salvar"** ou **"Aplicar"**
- Aguardar 2-5 minutos para propagação

## 🧪 **Teste de Verificação**

### **Antes da Configuração:**

```bash
# Windows PowerShell
Test-NetConnection -ComputerName 179.157.157.190 -Port 3000  # ❌ Falha
Test-NetConnection -ComputerName 179.157.157.190 -Port 5000  # ❌ Falha
Test-NetConnection -ComputerName 179.157.157.190 -Port 5001  # ❌ Falha
```

### **Depois da Configuração:**

```bash
# Windows PowerShell
Test-NetConnection -ComputerName 179.157.157.190 -Port 3000  # ✅ Sucesso
Test-NetConnection -ComputerName 179.157.157.190 -Port 5000  # ✅ Sucesso
Test-NetConnection -ComputerName 179.157.157.190 -Port 5001  # ✅ Sucesso
```

## 🌐 **URLs de Acesso (Após Configuração)**

| Serviço    | URL                         | Descrição           |
| ---------- | --------------------------- | ------------------- |
| Frontend   | http://179.157.157.190:3000 | Interface principal |
| RAG Server | http://179.157.157.190:5000 | Servidor de IA      |
| API Server | http://179.157.157.190:5001 | API REST            |

## ⚠️ **Considerações de Segurança**

### **Recomendações:**

- **Limitar origem**: Em vez de 0.0.0.0/0, considere limitar para IPs específicos
- **Monitoramento**: Verificar logs de acesso regularmente
- **Backup**: Documentar configurações atuais antes de alterar

### **Alternativas mais seguras:**

```
Origem: 179.157.157.0/24 (rede da Hostinger)
Origem: [SEU_IP_LOCAL]/32 (seu IP específico)
```

## 🆘 **Suporte e Alternativas**

### **Se não conseguir configurar:**

1. **Ticket de suporte**: Solicitar abertura das portas 3000, 5000, 5001
2. **Portas alternativas**: Usar 80, 443, 8080, 8443
3. **Proxy reverso**: Configurar nginx para redirecionamento

### **Contato Hostinger:**

- **Suporte técnico**: Via painel de controle
- **Chat online**: Disponível no site
- **Email**: suporte@hostinger.com.br

## 📝 **Comandos Úteis no Servidor**

### **Verificar status dos serviços:**

```bash
./status.sh
```

### **Reiniciar sistema:**

```bash
./stop_all.sh
./start_all.sh
```

### **Ver logs:**

```bash
tail -f logs/*.log
```

## 🔄 **Atualizações**

- **Data**: Agosto de 2025
- **Versão**: 1.0
- **Última revisão**: Configuração inicial do firewall

---

**⚠️ IMPORTANTE**: Sempre teste a conectividade após alterações no firewall!
