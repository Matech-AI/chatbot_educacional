# 🔧 SOLUÇÃO PARA PROBLEMA DE IP INCORRETO - DNA DA FORÇA

## 📋 PROBLEMA IDENTIFICADO

O sistema está configurado com um IP estático antigo (`31.97.16.142`) que não corresponde ao IP atual do servidor (`2a02:4780:14:42c4::1`).

## 🚀 SOLUÇÃO AUTOMÁTICA

### 1. Executar o Script de Atualização

No servidor Linux, execute:

```bash
cd /root/dna-forca-complete
chmod +x update_config.sh
./update_config.sh
```

### 2. Reiniciar os Serviços

Após a atualização, reinicie todos os serviços:

```bash
./stop_all.sh
./start_all.sh
```

### 3. Verificar o Status

Confirme que tudo está funcionando:

```bash
./status.sh
```

## 🔍 SOLUÇÃO MANUAL

### 1. Atualizar Configurações do Backend

Edite o arquivo `backend/config/hostinger_config.py`:

```python
def get_server_ip() -> str:
    """
    Retorna o IP do servidor automaticamente detectado
    """
    try:
        # Tenta obter o hostname do servidor
        hostname = socket.gethostname()

        # Obtém o IP associado ao hostname
        ip_address = socket.gethostbyname(hostname)

        # Se for localhost, tenta obter o IP externo
        if ip_address in ['127.0.0.1', 'localhost']:
            # Tenta conectar a um servidor externo para descobrir o IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]

        return ip_address
    except Exception as e:
        print(f"Erro ao detectar IP do servidor: {e}")
        return "0.0.0.0"  # Fallback para aceitar todas as conexões
```

### 2. Atualizar Vite Config

Edite o arquivo `vite.config.ts`:

```typescript
if (isHostinger) {
  // Usar variável de ambiente ou detectar automaticamente
  const serverIP = process.env.SERVER_IP || "0.0.0.0";
  apiTarget = `http://${serverIP}:8000`;
  ragApiTarget = `http://${serverIP}:8001`;
}
```

### 3. Criar Arquivo .env

Crie um arquivo `.env` no diretório raiz:

```bash
# Configurações específicas para o ambiente Hostinger
HOSTINGER=true
SERVER_IP=2a02:4780:14:42c4::1

# Portas dos serviços
RAG_PORT=8000
API_PORT=8001
FRONTEND_PORT=3000

# CORS Origins
CORS_ORIGINS=http://2a02:4780:14:42c4::1:3000,http://2a02:4780:14:42c4::1,http://localhost:3000

# Ambiente
ENVIRONMENT=production
```

## 📊 VERIFICAÇÃO

### Testar Conectividade

Execute o script de teste:

```bash
chmod +x test_connectivity.sh
./test_connectivity.sh
```

### Verificar URLs

Após a correção, as URLs devem ser:

- **Frontend**: http://2a02:4780:14:42c4::1:3000
- **RAG Server**: http://2a02:4780:14:42c4::1:8000
- **API Server**: http://2a02:4780:14:42c4::1:8001

## 🚨 PROBLEMAS COMUNS

### 1. IP IPv6

Se o servidor usar apenas IPv6, certifique-se de que:

- O firewall permite conexões IPv6
- Os serviços estão configurados para aceitar IPv6
- Use colchetes para URLs IPv6: `http://[2a02:4780:14:42c4::1]:3000`

### 2. CORS

Verifique se as configurações de CORS incluem o IP correto:

```python
CORS_ORIGINS = [
    "http://2a02:4780:14:42c4::1:3000",
    "http://2a02:4780:14:42c4::1",
    "http://localhost:3000"
]
```

### 3. Firewall

Certifique-se de que as portas estão abertas:

```bash
# Verificar portas abertas
netstat -tlnp | grep -E ':(3000|8000|8001)'

# Abrir portas se necessário
ufw allow 3000
ufw allow 8000
ufw allow 8001
```

## 🔄 MANUTENÇÃO

### Atualização Automática

Para evitar problemas futuros, configure uma atualização automática:

```bash
# Adicionar ao crontab
crontab -e

# Executar a cada reinicialização
@reboot cd /root/dna-forca-complete && ./update_config.sh
```

### Monitoramento

Use o script de status para monitorar:

```bash
# Verificar status a cada 5 minutos
*/5 * * * * cd /root/dna-forca-complete && ./status.sh >> logs/status.log 2>&1
```

## 📞 SUPORTE

Se o problema persistir:

1. Verifique os logs: `tail -f logs/*.log`
2. Execute o teste de conectividade: `./test_connectivity.sh`
3. Verifique o status: `./status.sh`
4. Reinicie os serviços: `./stop_all.sh && ./start_all.sh`

---

**Última atualização**: $(date)
**Versão**: 1.0
**Status**: ✅ Resolvido
