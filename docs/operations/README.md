# 🔧 Guia de Operações - Sistema RAG DNA da Força

Este guia explica como o Sistema RAG DNA da Força funciona em operação e como gerenciá-lo de forma eficiente.

## 🎯 **Visão Geral das Operações**

O Sistema RAG DNA da Força é composto por vários componentes que trabalham em conjunto para fornecer um chatbot educacional inteligente. Este guia explica como cada componente funciona e como gerenciá-los.

## 🏗️ **Arquitetura Operacional**

### **Componentes Principais:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Banco de      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Dados         │
│                 │    │                 │    │   (ChromaDB)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Supabase      │    │   Google Drive  │    │   IA Models     │
│   (Auth)        │    │   (Sync)        │    │   (OpenAI/      │
│                 │    │                 │    │    Anthropic)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Fluxo de Dados:**
1. **Usuário faz login** via Supabase
2. **Frontend se comunica** com Backend via API
3. **Backend processa** requisições e consulta IA
4. **ChromaDB fornece** contexto relevante
5. **IA gera resposta** baseada no contexto
6. **Resposta é retornada** ao usuário

## 🔄 **Ciclo de Vida das Operações**

### **1. Inicialização do Sistema**
```bash
# Sequência de inicialização
1. Banco de dados (ChromaDB + Supabase)
2. Serviços de autenticação
3. Sincronização com Google Drive
4. Backend API (FastAPI)
5. Frontend (React)
6. Sistema de IA (OpenAI/Anthropic)
```

### **2. Operação Normal**
```bash
# Durante operação normal
- Usuários fazem login/logout
- Chatbot responde perguntas
- Sistema sincroniza com Drive
- Logs são gerados
- Métricas são coletadas
```

### **3. Manutenção e Atualizações**
```bash
# Processo de atualização
1. Backup dos dados
2. Deploy da nova versão
3. Verificação de integridade
4. Rollback se necessário
5. Monitoramento pós-deploy
```

## 🗄️ **Gerenciamento de Banco de Dados**

### **ChromaDB (Banco Vetorial)**

#### **Operações Diárias:**
```bash
# Verificar status
curl http://localhost:5000/api/collections

# Verificar tamanho
du -sh backend/data/.chromadb/

# Verificar número de documentos
python -c "
import chromadb
client = chromadb.PersistentClient('backend/data/.chromadb')
for col in client.list_collections():
    print(f'{col.name}: {col.count()} documentos')
"
```

#### **Manutenção:**
```bash
# Limpeza de dados antigos
# O sistema mantém automaticamente, mas você pode:

# 1. Verificar integridade
python backend/scripts/check_db_integrity.py

# 2. Otimizar performance
python backend/scripts/optimize_db.py

# 3. Backup
cp -r backend/data/.chromadb backup/chromadb_$(date +%Y%m%d)
```

### **Supabase (Autenticação e Metadados)**

#### **Operações de Usuários:**
```bash
# Verificar usuários ativos
# Dashboard Supabase > Authentication > Users

# Verificar políticas de segurança
# Dashboard Supabase > Authentication > Policies

# Backup de dados de usuário
# Dashboard Supabase > Database > Backups
```

## 🤖 **Gerenciamento de IA e Chatbot**

### **Modelos de IA**

#### **Configuração:**
```python
# Configuração de modelos
AI_CONFIGS = {
    "openai": {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000
    },
    "anthropic": {
        "model": "claude-3-sonnet",
        "temperature": 0.7,
        "max_tokens": 2000
    }
}
```

#### **Monitoramento:**
```bash
# Verificar uso de API
# OpenAI: https://platform.openai.com/account/usage
# Anthropic: https://console.anthropic.com/account/usage

# Verificar logs de IA
tail -f backend/logs/ai_requests.log

# Métricas de performance
curl http://localhost:5000/api/metrics/ai
```

### **Sistema de Prompts**

#### **Gerenciamento:**
```python
# Os prompts são configurados em:
# backend/data/assistant_configs.json

# Para atualizar prompts:
1. Edite o arquivo de configuração
2. Reinicie o backend
3. Teste com usuários
4. Monitore qualidade das respostas
```

## ☁️ **Sincronização com Google Drive**

### **Operação Automática**

#### **Como Funciona:**
1. **Sistema verifica** pasta do Drive periodicamente
2. **Novos arquivos** são detectados automaticamente
3. **Arquivos são baixados** e processados
4. **Embeddings são gerados** e indexados
5. **Metadados são atualizados** no banco

#### **Monitoramento:**
```bash
# Verificar status da sincronização
curl http://localhost:5000/api/sync/status

# Verificar logs de sincronização
tail -f backend/logs/drive_sync.log

# Verificar arquivos sincronizados
ls -la backend/data/materials/
```

### **Manutenção da Sincronização**

#### **Problemas Comuns:**
```bash
# 1. Quota excedida
# Solução: Aguarde reset da quota ou aumente limites

# 2. Credenciais expiradas
# Solução: Renove credenciais no Google Cloud Console

# 3. Arquivos corrompidos
# Solução: Execute reparo automático
python backend/scripts/repair_sync.py
```

## 📊 **Monitoramento e Métricas**

### **Métricas do Sistema**

#### **Performance:**
```bash
# Response time
curl http://localhost:5000/api/metrics/performance

# Uso de memória
curl http://localhost:5000/api/metrics/memory

# Uso de CPU
curl http://localhost:5000/api/metrics/cpu
```

#### **Negócio:**
```bash
# Usuários ativos
curl http://localhost:5000/api/metrics/users

# Perguntas respondidas
curl http://localhost:5000/api/metrics/questions

# Qualidade das respostas
curl http://localhost:5000/api/metrics/quality
```

### **Alertas e Notificações**

#### **Configuração:**
```python
# Alertas automáticos para:
ALERTS = {
    "high_memory": "Uso de memória > 80%",
    "high_cpu": "Uso de CPU > 90%",
    "api_errors": "Taxa de erro > 5%",
    "sync_failure": "Falha na sincronização",
    "ai_timeout": "Timeout na IA > 30s"
}
```

## 🔒 **Segurança e Compliance**

### **Autenticação e Autorização**

#### **Políticas de Segurança:**
```sql
-- Exemplo de política Supabase
CREATE POLICY "Users can only access their own data" ON users
FOR ALL USING (auth.uid() = id);

CREATE POLICY "Public read access to materials" ON materials
FOR SELECT USING (true);
```

#### **Auditoria:**
```bash
# Logs de auditoria
tail -f backend/logs/audit.log

# Verificar acessos suspeitos
python backend/scripts/security_audit.py
```

### **Proteção de Dados**

#### **Backup e Recuperação:**
```bash
# Backup automático diário
0 2 * * * /usr/bin/python backend/scripts/backup.py

# Backup manual
python backend/scripts/backup.py --full

# Restauração
python backend/scripts/restore.py --backup=20240828
```

## 🚨 **Gestão de Incidentes**

### **Classificação de Incidentes**

#### **Crítico (P0):**
- Sistema completamente inacessível
- Perda de dados
- Violação de segurança

#### **Alto (P1):**
- Funcionalidades principais quebradas
- Performance severamente degradada
- Falhas de autenticação

#### **Médio (P2):**
- Funcionalidades secundárias quebradas
- Performance moderadamente degradada
- Problemas de sincronização

#### **Baixo (P3):**
- Problemas de UX
- Melhorias e otimizações
- Documentação

### **Processo de Resolução**

#### **1. Detecção**
```bash
# Monitoramento automático
# Alertas em tempo real
# Relatórios de usuários
```

#### **2. Triagem**
```bash
# Classificar severidade
# Atribuir responsável
# Estimar tempo de resolução
```

#### **3. Resolução**
```bash
# Implementar correção
# Testar solução
# Deploy em produção
```

#### **4. Pós-Incidente**
```bash
# Documentar incidente
# Analisar causa raiz
# Implementar prevenção
```

## 📈 **Otimização e Performance**

### **Otimizações de Sistema**

#### **Backend:**
```python
# 1. Cache de embeddings
@lru_cache(maxsize=1000)
def get_embedding(text):
    return embedding_model.encode(text)

# 2. Processamento assíncrono
async def process_documents(docs):
    tasks = [process_doc(doc) for doc in docs]
    return await asyncio.gather(*tasks)

# 3. Rate limiting
@limiter.limit("100/minute")
async def api_endpoint():
    pass
```

#### **Frontend:**
```javascript
// 1. Lazy loading de componentes
const LazyComponent = React.lazy(() => import('./Component'));

// 2. Cache de requisições
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 5 * 60 * 1000, // 5 minutos
        },
    },
});

// 3. Debounce de inputs
const debouncedSearch = useDebounce(searchTerm, 300);
```

### **Métricas de Performance**

#### **KPIs Importantes:**
- **Response Time:** < 2 segundos
- **Throughput:** > 100 req/min
- **Error Rate:** < 1%
- **Uptime:** > 99.9%
- **Memory Usage:** < 80%

## 🔄 **Deploy e Atualizações**

### **Estratégia de Deploy**

#### **Blue-Green Deployment:**
```bash
# 1. Deploy nova versão em ambiente paralelo
docker-compose -f docker-compose.new.yml up -d

# 2. Teste a nova versão
curl http://localhost:5001/health

# 3. Switch de tráfego
# Atualize load balancer ou proxy

# 4. Desligue versão antiga
docker-compose down
```

#### **Rollback Automático:**
```bash
# Se métricas piorarem após deploy
if error_rate > 5% or response_time > 5s:
    rollback_to_previous_version()
    alert_team("Rollback executado automaticamente")
```

### **Testes Pós-Deploy**

#### **Checklist de Verificação:**
```bash
# 1. Health checks
curl http://localhost:5000/health

# 2. Funcionalidades críticas
- Login de usuário
- Chatbot responde
- Sincronização funciona
- Upload de arquivos

# 3. Métricas de performance
- Response time
- Error rate
- Memory usage
- CPU usage
```

## 📚 **Documentação Operacional**

### **Runbooks**

#### **Runbook de Deploy:**
```markdown
# Deploy em Produção

## Pré-requisitos
- [ ] Testes passando
- [ ] Code review aprovado
- [ ] Backup executado
- [ ] Equipe notificada

## Passos
1. Tag da versão
2. Deploy automático
3. Verificação de saúde
4. Testes de fumaça
5. Monitoramento pós-deploy
```

#### **Runbook de Incidentes:**
```markdown
# Sistema Inacessível

## Diagnóstico
1. Verificar status dos serviços
2. Verificar logs de erro
3. Verificar recursos do sistema

## Ações Imediatas
1. Reiniciar serviços críticos
2. Notificar equipe
3. Executar procedimentos de emergência
```

## 🎯 **Melhorias Contínuas**

### **Processo de Melhoria**

#### **1. Coleta de Feedback**
- **Usuários:** Qualidade das respostas, UX
- **Equipe:** Performance, manutenibilidade
- **Sistema:** Métricas, logs, alertas

#### **2. Análise de Dados**
- **Trends:** Uso, performance, erros
- **Bottlenecks:** Identificar gargalos
- **Oportunidades:** Melhorias possíveis

#### **3. Implementação**
- **Priorização:** Baseada em impacto
- **Desenvolvimento:** Iterativo e incremental
- **Validação:** Testes e métricas

### **Métricas de Sucesso**

#### **Técnicas:**
- **Performance:** Response time, throughput
- **Estabilidade:** Uptime, error rate
- **Eficiência:** Resource usage, cost

#### **Negócio:**
- **Usuários:** Ativos, retenção, satisfação
- **Qualidade:** Precisão das respostas
- **Adoção:** Uso das funcionalidades

---

## 📞 **Suporte e Comunicação**

### **Canais de Comunicação**
- **Equipe:** Slack/Discord interno
- **Usuários:** GitHub Issues, Email
- **Emergências:** PagerDuty, SMS

### **Escalação**
- **Nível 1:** Equipe de desenvolvimento
- **Nível 2:** DevOps/SRE
- **Nível 3:** Arquitetos/CTO

---

**📅 Última atualização:** Agosto 2025  
**🔄 Versão:** 2.0.0  
**👨‍💻 Mantido por:** Equipe DNA da Força
