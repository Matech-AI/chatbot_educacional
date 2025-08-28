# 🔍 Visualizador 3D do Banco de Dados Vetorial

Este script permite visualizar e analisar o banco de dados vetorial (ChromaDB) do sistema RAG em **3D interativo**!

## 🚀 **Funcionalidades Principais:**

### **🎯 Visualizações 3D:**

- **PCA 3D**: Redução de dimensionalidade com Análise de Componentes Principais
- **UMAP 3D**: Redução de dimensionalidade com UMAP (mais preserva estrutura local)
- **Clustering automático**: Agrupamento K-means dos documentos por similaridade

### **📊 Análises 2D:**

- **Comparação de métodos**: PCA, t-SNE e UMAP lado a lado
- **Análise de similaridade**: Matriz de similaridade entre documentos
- **Heatmaps interativos**: Visualização da similaridade entre todos os documentos

### **💾 Exportação:**

- **HTML interativo**: Visualizações que podem ser abertas no navegador
- **PNG/PDF**: Imagens estáticas para relatórios
- **Relatório completo**: HTML com todas as visualizações integradas

## 📦 **Instalação das Dependências:**

```bash
# Instalar todas as dependências necessárias
pip install -r requirements_visualizer.txt

# Ou instalar individualmente:
pip install plotly scikit-learn umap-learn matplotlib seaborn chromadb
```

## 🎮 **Como Usar:**

### **1. Executar o Script:**

```bash
cd backend
python visualize_vector_db.py
```

### **2. Selecionar Coleção:**

O script mostrará todas as coleções disponíveis no ChromaDB:

```
📚 Coleções disponíveis:
   1. dna_forca_collection (53,621 documentos)
   2. outra_colecao (1,234 documentos)

🎯 Selecione uma coleção (1-2): 1
```

### **3. Menu de Opções:**

```
🔧 Menu de Visualizações - dna_forca_collection
1. Visualização 3D (PCA)
2. Visualização 3D (UMAP)
3. Comparação 2D (PCA, t-SNE, UMAP)
4. Análise de Similaridade
5. Gerar Relatório Completo
6. Sair
```

## 🔍 **Exemplos de Visualizações:**

### **🎯 Visualização 3D com PCA:**

- **Eixo X**: Primeira componente principal
- **Eixo Y**: Segunda componente principal
- **Eixo Z**: Terceira componente principal
- **Cores**: Clusters automáticos (K-means)
- **Interatividade**: Zoom, rotação, hover com informações

### **🌌 Visualização 3D com UMAP:**

- **Preserva estrutura local** melhor que PCA
- **Clusters mais naturais** dos documentos
- **Melhor separação** de tópicos relacionados

### **📈 Comparação 2D:**

- **PCA**: Visão global da estrutura dos dados
- **t-SNE**: Foco em clusters locais
- **UMAP**: Balance entre global e local

### **🔥 Matriz de Similaridade:**

- **Cores**: Similaridade entre documentos (0-1)
- **Padrões**: Identifica grupos de documentos relacionados
- **Diagnóstico**: Detecta documentos muito similares ou únicos

## 📊 **Interpretação dos Resultados:**

### **🎯 Clusters (Agrupamentos):**

- **Cluster 0**: Documentos sobre hipertrofia muscular
- **Cluster 1**: Documentos sobre periodização
- **Cluster 2**: Documentos sobre biomecânica
- **Cluster 3**: Documentos sobre nutrição
- **Cluster 4**: Documentos sobre recuperação

### **🔗 Similaridade:**

- **0.9-1.0**: Documentos quase idênticos
- **0.7-0.9**: Documentos muito similares
- **0.5-0.7**: Documentos moderadamente similares
- **0.3-0.5**: Documentos pouco similares
- **0.0-0.3**: Documentos diferentes

### **📈 Métricas:**

- **Similaridade Média**: Qual a similaridade geral dos documentos
- **Desvio Padrão**: Quão variados são os documentos
- **Total de Documentos**: Quantos documentos foram processados

## 🚨 **Troubleshooting:**

### **❌ Erro: "Dependências não encontradas"**

```bash
pip install plotly scikit-learn umap-learn matplotlib seaborn
```

### **❌ Erro: "Diretório ChromaDB não encontrado"**

- Verifique se o caminho `data/.chromadb` existe
- Execute o RAG server primeiro para criar o banco

### **❌ Erro: "Falha ao carregar coleção"**

- Verifique se a coleção tem documentos
- Verifique se os embeddings foram gerados

### **❌ Visualizações lentas:**

- Reduza o número de clusters (padrão: 5)
- Use PCA em vez de UMAP para coleções grandes
- Considere amostrar documentos para análise inicial

## 💡 **Dicas de Uso:**

### **🎯 Para Análise Rápida:**

1. Use **PCA 3D** para visão geral
2. Aplique **5 clusters** para identificação de tópicos
3. Exporte como **HTML** para compartilhamento

### **🔍 Para Análise Detalhada:**

1. Compare **PCA vs UMAP** para entender estrutura
2. Analise **matriz de similaridade** para padrões
3. Gere **relatório completo** para documentação

### **📊 Para Relatórios:**

1. Use **opção 5** para relatório completo
2. Exporte visualizações em **PNG/PDF**
3. Integre no **relatório HTML** gerado

## 🎨 **Personalização:**

### **🔧 Ajustar Número de Clusters:**

```python
# No código, linha ~200
clusters = self.cluster_documents(embeddings, n_clusters=10)  # Mudar de 5 para 10
```

### **🎨 Mudar Cores:**

```python
# No código, linha ~220
colors = px.colors.qualitative.Set1  # Mudar paleta de cores
```

### **📏 Ajustar Tamanho dos Pontos:**

```python
# No código, linha ~225
marker=dict(size=12, ...)  # Mudar de 8 para 12
```

## 🚀 **Casos de Uso:**

### **🔍 Debug do Sistema RAG:**

- Identificar documentos muito similares
- Detectar clusters de tópicos
- Verificar qualidade dos embeddings

### **📚 Análise de Conteúdo:**

- Mapear estrutura dos materiais
- Identificar lacunas de conteúdo
- Planejar organização de documentos

### **🎓 Pesquisa e Desenvolvimento:**

- Comparar diferentes modelos de embedding
- Otimizar parâmetros de clustering
- Validar qualidade da indexação

---

**🎯 Resultado:** Visualização completa e interativa do seu banco de dados vetorial, permitindo entender como os documentos estão organizados semanticamente!
