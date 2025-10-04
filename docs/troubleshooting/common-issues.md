# 🚨 Problemas Comuns e Soluções - Sistema RAG DNA da Força

Este guia aborda os problemas mais frequentes encontrados no Sistema RAG DNA da Força e suas respectivas soluções.

## 🔍 **Problemas de Autenticação**

### **❌ Erro: "Invalid credentials" ou "Authentication failed"**

#### **Sintomas:**
- Usuário não consegue fazer login
- Mensagem de erro de credenciais inválidas
- Redirecionamento para página de login

#### **Causas Possíveis:**
1. **Chaves do Supabase incorretas**
2. **Usuário não existe no banco**
3. **Políticas de segurança mal configuradas**
4. **Token expirado**

#### **Soluções:**
```bash
# 1. Verifique as variáveis de ambiente
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# 2. Teste a conexão com Supabase
curl -X GET "$SUPABASE_URL/rest/v1/" \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY"

# 3. Verifique se o usuário existe
# Acesse o dashboard do Supabase > Authentication > Users
```

#### **Prevenção:**
- Configure corretamente as variáveis de ambiente
- Teste a autenticação após mudanças
- Monitore os logs de autenticação

---

### **❌ Erro: "CORS policy" ou "Cross-origin request blocked"**

#### **Sintomas:**
- Erro no console do navegador sobre CORS
- Requisições bloqueadas pelo navegador
- Frontend não consegue se comunicar com backend

#### **Soluções:**
```python
# Backend - Configure CORS corretamente
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://seu-frontend.com", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

```bash
# Frontend - Verifique a URL da API
VITE_API_URL=https://seu-backend.com
# Não http://localhost:5000 em produção
```

---

## 🤖 **Problemas com IA e Chatbot**

### **❌ Erro: "OpenAI API key not found" ou "Rate limit exceeded"**

#### **Sintomas:**
- Chatbot não responde
- Erro de API key inválida
- Limite de requisições excedido

#### **Soluções:**
```bash
# 1. Verifique a API key
echo $OPENAI_API_KEY

# 2. Teste a API OpenAI
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# 3. Verifique o saldo da conta
# Acesse https://platform.openai.com/account/usage
```

#### **Alternativas:**
```bash
# Use Anthropic como fallback
ANTHROPIC_API_KEY=your_key_here

# Ou configure múltiplos provedores
AI_PROVIDERS=["openai", "anthropic", "local"]
```

---

### **❌ Erro: "Context too long" ou "Token limit exceeded"**

#### **Sintomas:**
- Respostas truncadas
- Erro de limite de tokens
- Performance lenta

#### **Soluções:**
```python
# 1. Reduza o tamanho do contexto
MAX_CONTEXT_LENGTH = 4000  # Reduza de 5000 para 4000

# 2. Implemente chunking inteligente
def smart_chunking(text, max_length=4000):
    # Divide o texto em chunks menores
    # Mantém contexto relevante
    pass

# 3. Use resumo de contexto
def summarize_context(context):
    # Resume o contexto para caber nos tokens
    pass
```

---

## 🗄️ **Problemas com Banco de Dados**

### **❌ Erro: "ChromaDB connection failed" ou "Collection not found"**

#### **Sintomas:**
- Sistema não consegue acessar o banco vetorial
- Erro ao buscar documentos
- Performance muito lenta

#### **Soluções:**
```bash
# 1. Verifique se o ChromaDB está rodando
ps aux | grep chromadb

# 2. Verifique o diretório de dados
ls -la backend/data/.chromadb/

# 3. Reinicie o ChromaDB
rm -rf backend/data/.chromadb/
# O sistema recriará automaticamente
```

#### **Otimizações:**
```python
# Configure parâmetros de performance
CHROMA_SETTINGS = {
    "anonymized_telemetry": False,
    "is_persistent": True,
    "persist_directory": "data/.chromadb"
}
```

---

### **❌ Erro: "Memory error" ou "Out of memory"**

#### **Sintomas:**
- Sistema trava ou crasha
- Erro de memória insuficiente
- Performance degradada

#### **Soluções:**
```python
# 1. Reduza o tamanho dos chunks
CHUNK_SIZE = 500  # Reduza de 1000 para 500

# 2. Implemente processamento em lotes
def process_in_batches(documents, batch_size=100):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        process_batch(batch)

# 3. Use streaming para arquivos grandes
def stream_process_file(file_path):
    with open(file_path, 'r') as f:
        for chunk in iter(lambda: f.read(1024), ""):
            yield process_chunk(chunk)
```

---

## ☁️ **Problemas de Sincronização com Google Drive**

### **❌ Erro: "Google Drive API quota exceeded" ou "Authentication failed"**

#### **Sintomas:**
- Sincronização para de funcionar
- Erro de quota excedida
- Arquivos não são baixados

#### **Soluções:**
```bash
# 1. Verifique as credenciais
ls -la backend/token.json

# 2. Renove as credenciais do Google Cloud
# Acesse https://console.cloud.google.com/
# Crie novas credenciais de serviço

# 3. Verifique a quota da API
# Google Cloud Console > APIs & Services > Quotas
```

#### **Alternativas:**
```python
# Implemente retry com backoff exponencial
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def sync_with_retry():
    # Tenta sincronizar com retry automático
    pass
```

---

## 🌐 **Problemas de Deploy e Infraestrutura**

### **❌ Erro: "Port already in use" ou "Address already in use"**

#### **Sintomas:**
- Servidor não inicia
- Erro de porta já em uso
- Conflito de serviços

#### **Soluções:**
```bash
# 1. Encontre o processo usando a porta
lsof -i :5000
# ou
netstat -tulpn | grep :5000

# 2. Mate o processo
kill -9 <PID>

# 3. Ou use uma porta diferente
PORT=5001 python main.py
```

---

### **❌ Erro: "Docker container failed" ou "Container exited with code 1"**

#### **Sintomas:**
- Container para de funcionar
- Erro de inicialização
- Logs mostram erro de saída

#### **Soluções:**
```bash
# 1. Verifique os logs do container
docker logs <container_name>

# 2. Reinicie o container
docker restart <container_name>

# 3. Rebuild da imagem
docker-compose down
docker-compose up -d --build

# 4. Verifique recursos disponíveis
docker system df
docker stats
```

---

## 📱 **Problemas de Frontend**

### **❌ Erro: "Build failed" ou "Module not found"**

#### **Sintomas:**
- Frontend não compila
- Erro de módulo não encontrado
- Dependências quebradas

#### **Soluções:**
```bash
# 1. Limpe e reinstale dependências
rm -rf node_modules package-lock.json
npm install

# 2. Verifique versões das dependências
npm list

# 3. Atualize dependências
npm update

# 4. Verifique compatibilidade de versões
npm audit
```

---

### **❌ Erro: "Runtime error" ou "JavaScript error"**

#### **Sintomas:**
- Erro no console do navegador
- Página não carrega completamente
- Funcionalidades quebradas

#### **Soluções:**
```javascript
// 1. Adicione error boundaries
class ErrorBoundary extends React.Component {
    componentDidCatch(error, errorInfo) {
        console.error('Error:', error);
        console.error('Error Info:', errorInfo);
    }
}

// 2. Implemente logging de erros
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    // Envie para serviço de logging
});

// 3. Verifique variáveis de ambiente
console.log('API URL:', import.meta.env.VITE_API_URL);
```

---

## 🔧 **Problemas de Performance**

### **❌ Sistema Lento ou "Request timeout"**

#### **Sintomas:**
- Respostas lentas
- Timeout de requisições
- Interface travando

#### **Soluções:**
```python
# 1. Implemente cache
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(data):
    # Cache para operações custosas
    pass

# 2. Use async/await para operações I/O
async def process_documents(documents):
    tasks = [process_doc(doc) for doc in documents]
    results = await asyncio.gather(*tasks)
    return results

# 3. Implemente rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
limiter = Limiter(key_func=get_remote_address)
```

---

## 📊 **Monitoramento e Debug**

### **🔍 Como Identificar Problemas**

#### **1. Logs do Sistema:**
```bash
# Backend logs
tail -f backend/logs/app.log
tail -f backend/logs/error.log

# Docker logs
docker logs -f <container_name>

# Render logs (se usando Render)
# Dashboard > Logs
```

#### **2. Métricas de Performance:**
```bash
# Uso de recursos
htop
df -h
free -h

# Portas e conexões
netstat -tulpn
ss -tulpn

# Processos Python
ps aux | grep python
```

#### **3. Testes de Conectividade:**
```bash
# Teste da API
curl -v http://localhost:5000/health

# Teste do banco
curl -v http://localhost:5000/api/collections

# Teste de autenticação
curl -v -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/user/profile
```

---

## 🚨 **Problemas Críticos**

### **❌ Sistema Completamente Inacessível**

#### **Checklist de Emergência:**
1. **Verifique se os serviços estão rodando**
2. **Verifique logs de erro**
3. **Verifique recursos do sistema**
4. **Verifique conectividade de rede**
5. **Verifique configurações de firewall**

#### **Ações Imediatas:**
```bash
# 1. Reinicie os serviços críticos
sudo systemctl restart nginx
sudo systemctl restart docker

# 2. Verifique espaço em disco
df -h

# 3. Verifique uso de memória
free -h

# 4. Verifique processos
ps aux | head -20
```

---

## 📞 **Quando Pedir Ajuda**

### **🔴 Problemas Críticos (Ajuda Imediata):**
- Sistema completamente inacessível
- Perda de dados
- Problemas de segurança
- Falhas de produção

### **🟡 Problemas Moderados (Ajuda em 24h):**
- Funcionalidades quebradas
- Performance degradada
- Problemas de sincronização
- Erros de autenticação

### **🟢 Problemas Menores (Ajuda em 72h):**
- Melhorias de UX
- Otimizações
- Documentação
- Novas features

---

## 🆘 **Recursos de Ajuda**

### **📖 Documentação:**
- [Guia de Deploy](../deploy/README.md)
- [Sistema RAG](../rag/README.md)
- [Desenvolvimento Local](../development/local-development.md)

### **🐛 Issues e Suporte:**
- **GitHub Issues:** [Reporte problemas](https://github.com/seu-repo/issues)
- **Discord:** [Comunidade ativa](https://discord.gg/dnadaforca)
- **Email:** suporte@dnadaforca.com

### **🔧 Ferramentas de Debug:**
- **Logs do sistema** - Para identificar problemas
- **Métricas de performance** - Para otimização
- **Testes automatizados** - Para validação
- **Monitoramento em tempo real** - Para alertas

---

## 🎯 **Prevenção de Problemas**

### **✅ Boas Práticas:**
1. **Monitore logs** regularmente
2. **Configure alertas** para problemas críticos
3. **Teste mudanças** em ambiente de desenvolvimento
4. **Mantenha backups** regulares
5. **Documente configurações** importantes
6. **Use versionamento** para mudanças
7. **Implemente health checks** automáticos

### **📅 Manutenção Preventiva:**
- **Diária:** Verificar logs e métricas
- **Semanal:** Análise de performance
- **Mensal:** Atualização de dependências
- **Trimestral:** Revisão de segurança

---

**📅 Última atualização:** Agosto 2025  
**🔄 Versão:** 2.0.0  
**👨‍💻 Mantido por:** Equipe DNA da Força
