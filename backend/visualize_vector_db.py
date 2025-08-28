#!/usr/bin/env python3
"""
Visualizador 3D do Banco de Dados Vetorial (ChromaDB)
Permite visualizar os embeddings dos documentos em 3D para análise e debug.

Funcionalidades:
- Visualização 3D com PCA, t-SNE e UMAP
- Clustering automático dos documentos
- Interatividade com plotly
- Análise de similaridade entre documentos
- Exportação de visualizações

Autor: Sistema RAG DNA da Força
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
import time

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adicionar o diretório raiz ao path para imports
sys.path.append(str(Path(__file__).parent))

try:
    import chromadb
    from chromadb.config import Settings
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    import umap
    from collections import defaultdict
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError as e:
    logger.error(f"❌ Dependências não encontradas: {e}")
    logger.info("💡 Instale com: pip install plotly scikit-learn umap-learn matplotlib seaborn")
    sys.exit(1)

class VectorDBVisualizer:
    """Visualizador 3D do banco de dados vetorial"""
    
    def __init__(self, persist_dir: str = "data/.chromadb"):
        self.persist_dir = Path(persist_dir)
        self.client = None
        self.collections = {}
        self.embeddings = {}
        self.metadata = {}
        self.documents = {}
        
    def connect_to_chromadb(self) -> bool:
        """Conecta ao ChromaDB e carrega as coleções"""
        try:
            if not self.persist_dir.exists():
                logger.error(f"❌ Diretório ChromaDB não encontrado: {self.persist_dir}")
                return False
                
            # Conectar ao ChromaDB
            self.client = chromadb.PersistentClient(path=str(self.persist_dir))
            logger.info(f"✅ Conectado ao ChromaDB em: {self.persist_dir}")
            
            # Listar coleções
            collections = self.client.list_collections()
            logger.info(f"📚 Coleções encontradas: {len(collections)}")
            
            for collection in collections:
                logger.info(f"   - {collection.name}: {collection.count()} documentos")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao ChromaDB: {e}")
            return False
    
    def load_collection_data(self, collection_name: str) -> bool:
        """Carrega dados de uma coleção específica"""
        try:
            collection = self.client.get_collection(collection_name)
            
            # Obter todos os documentos
            results = collection.get(
                include=['embeddings', 'documents', 'metadatas']
            )
            
            self.collections[collection_name] = collection
            self.embeddings[collection_name] = np.array(results['embeddings'])
            self.documents[collection_name] = results['documents']
            self.metadata[collection_name] = results['metadatas']
            
            logger.info(f"✅ Coleção '{collection_name}' carregada:")
            logger.info(f"   - Embeddings: {self.embeddings[collection_name].shape}")
            logger.info(f"   - Documentos: {len(self.documents[collection_name])}")
            logger.info(f"   - Metadados: {len(self.metadata[collection_name])}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar coleção '{collection_name}': {e}")
            return False
    
    def reduce_dimensions(self, embeddings: np.ndarray, method: str = "pca", n_components: int = 3) -> np.ndarray:
        """Reduz dimensionalidade dos embeddings para visualização"""
        try:
            logger.info(f"🔧 Reduzindo dimensionalidade com {method.upper()}...")
            
            if method.lower() == "pca":
                reducer = PCA(n_components=n_components, random_state=42)
                reduced = reducer.fit_transform(embeddings)
                explained_variance = reducer.explained_variance_ratio_
                logger.info(f"✅ PCA: Variância explicada: {explained_variance}")
                
            elif method.lower() == "tsne":
                reducer = TSNE(n_components=n_components, random_state=42, perplexity=min(30, len(embeddings)-1))
                reduced = reducer.fit_transform(embeddings)
                logger.info(f"✅ t-SNE: Dimensionalidade reduzida para {n_components}D")
                
            elif method.lower() == "umap":
                reducer = umap.UMAP(n_components=n_components, random_state=42, n_neighbors=min(15, len(embeddings)-1))
                reduced = reducer.fit_transform(embeddings)
                logger.info(f"✅ UMAP: Dimensionalidade reduzida para {n_components}D")
                
            else:
                raise ValueError(f"Método não suportado: {method}")
            
            return reduced
            
        except Exception as e:
            logger.error(f"❌ Erro na redução de dimensionalidade: {e}")
            return None
    
    def cluster_documents(self, embeddings: np.ndarray, n_clusters: int = 5) -> np.ndarray:
        """Aplica clustering K-means aos documentos"""
        try:
            logger.info(f"🎯 Aplicando clustering K-means com {n_clusters} clusters...")
            
            # Normalizar embeddings
            scaler = StandardScaler()
            embeddings_scaled = scaler.fit_transform(embeddings)
            
            # Aplicar K-means
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(embeddings_scaled)
            
            logger.info(f"✅ Clustering aplicado: {len(np.unique(clusters))} clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"❌ Erro no clustering: {e}")
            return None
    
    def create_3d_scatter(self, collection_name: str, method: str = "pca", n_clusters: int = 5) -> go.Figure:
        """Cria visualização 3D interativa dos embeddings"""
        try:
            embeddings = self.embeddings[collection_name]
            documents = self.documents[collection_name]
            metadata = self.metadata[collection_name]
            
            # Reduzir dimensionalidade
            reduced_embeddings = self.reduce_dimensions(embeddings, method)
            if reduced_embeddings is None:
                raise ValueError("Falha na redução de dimensionalidade")
            
            # Aplicar clustering
            clusters = self.cluster_documents(embeddings, n_clusters)
            if clusters is None:
                clusters = np.zeros(len(embeddings), dtype=int)
            
            # Criar DataFrame para plotagem
            df = pd.DataFrame({
                'x': reduced_embeddings[:, 0],
                'y': reduced_embeddings[:, 1],
                'z': reduced_embeddings[:, 2],
                'cluster': clusters,
                'document': [doc[:100] + "..." if len(doc) > 100 else doc for doc in documents],
                'source': [meta.get('source', 'N/A') if meta else 'N/A' for meta in metadata]
            })
            
            # Criar figura 3D
            fig = go.Figure()
            
            # Adicionar pontos por cluster
            colors = px.colors.qualitative.Set3
            for cluster_id in sorted(df['cluster'].unique()):
                cluster_data = df[df['cluster'] == cluster_id]
                
                fig.add_trace(go.Scatter3d(
                    x=cluster_data['x'],
                    y=cluster_data['y'],
                    z=cluster_data['z'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=colors[cluster_id % len(colors)],
                        opacity=0.8
                    ),
                    text=cluster_data['document'],
                    hovertemplate='<b>Documento:</b> %{text}<br>' +
                                '<b>Fonte:</b> %{customdata}<br>' +
                                '<b>Cluster:</b> ' + str(cluster_id) + '<br>' +
                                '<b>Coordenadas:</b> (%{x:.2f}, %{y:.2f}, %{z:.2f})<extra></extra>',
                    customdata=cluster_data['source'],
                    name=f'Cluster {cluster_id}',
                    showlegend=True
                ))
            
            # Configurar layout
            fig.update_layout(
                title=f"Visualização 3D - {collection_name} ({method.upper()})",
                scene=dict(
                    xaxis_title=f"{method.upper()} Componente 1",
                    yaxis_title=f"{method.upper()} Componente 2",
                    zaxis_title=f"{method.upper()} Componente 3",
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.5)
                    )
                ),
                width=1000,
                height=800,
                showlegend=True
            )
            
            logger.info(f"✅ Visualização 3D criada para '{collection_name}'")
            return fig
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar visualização 3D: {e}")
            return None
    
    def create_2d_visualizations(self, collection_name: str) -> go.Figure:
        """Cria visualizações 2D com diferentes métodos"""
        try:
            embeddings = self.embeddings[collection_name]
            documents = self.documents[collection_name]
            metadata = self.metadata[collection_name]
            
            # Reduzir dimensionalidade para 2D com diferentes métodos
            methods = ["pca", "tsne", "umap"]
            reduced_data = {}
            
            for method in methods:
                reduced = self.reduce_dimensions(embeddings, method, n_components=2)
                if reduced is not None:
                    reduced_data[method] = reduced
            
            # Criar subplots
            fig = make_subplots(
                rows=1, cols=len(reduced_data),
                subplot_titles=[f"{method.upper()}" for method in reduced_data.keys()],
                specs=[[{"type": "scatter"} for _ in reduced_data]]
            )
            
            # Adicionar pontos para cada método
            colors = px.colors.qualitative.Set3
            for i, (method, reduced) in enumerate(reduced_data.items()):
                fig.add_trace(
                    go.Scatter(
                        x=reduced[:, 0],
                        y=reduced[:, 1],
                        mode='markers',
                        marker=dict(
                            size=6,
                            color=colors[i % len(colors)],
                            opacity=0.7
                        ),
                        text=[doc[:50] + "..." if len(doc) > 50 else doc for doc in documents],
                        hovertemplate='<b>Documento:</b> %{text}<br>' +
                                    '<b>Coordenadas:</b> (%{x:.2f}, %{y:.2f})<extra></extra>',
                        name=method.upper(),
                        showlegend=False
                    ),
                    row=1, col=i+1
                )
            
            # Configurar layout
            fig.update_layout(
                title=f"Comparação de Métodos de Redução - {collection_name}",
                width=1200,
                height=400,
                showlegend=False
            )
            
            logger.info(f"✅ Visualizações 2D criadas para '{collection_name}'")
            return fig
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar visualizações 2D: {e}")
            return None
    
    def analyze_similarity(self, collection_name: str, n_samples: int = 10, max_documents: int = 1000) -> Dict[str, Any]:
        """Analisa similaridade entre documentos com otimização de memória"""
        try:
            embeddings = self.embeddings[collection_name]
            documents = self.documents[collection_name]
            
            # 🚨 OTIMIZAÇÃO DE MEMÓRIA: Limitar número de documentos para análise
            total_docs = len(embeddings)
            if total_docs > max_documents:
                logger.warning(f"⚠️ Coleção muito grande ({total_docs} documentos)")
                logger.info(f"💡 Limitando análise para {max_documents} documentos para economizar memória")
                logger.info(f"💡 Use 'max_documents' maior se tiver mais RAM disponível")
                
                # Amostragem aleatória para economizar memória
                import random
                random.seed(42)  # Para reprodutibilidade
                indices = random.sample(range(total_docs), max_documents)
                embeddings_sample = embeddings[indices]
                documents_sample = [documents[i] for i in indices]
                actual_n_samples = min(n_samples, max_documents)
            else:
                embeddings_sample = embeddings
                documents_sample = documents
                actual_n_samples = n_samples
            
            logger.info(f"🔍 Analisando similaridade para {len(embeddings_sample)} documentos...")
            
            # Calcular matriz de similaridade (cosseno) com otimização de memória
            try:
                # Normalizar embeddings
                embeddings_norm = embeddings_sample / np.linalg.norm(embeddings_sample, axis=1, keepdims=True)
                
                # Calcular similaridade em chunks para economizar memória
                chunk_size = min(100, len(embeddings_sample))
                similarity_matrix = np.zeros((len(embeddings_sample), len(embeddings_sample)), dtype=np.float32)
                
                for i in range(0, len(embeddings_sample), chunk_size):
                    end_i = min(i + chunk_size, len(embeddings_sample))
                    for j in range(0, len(embeddings_sample), chunk_size):
                        end_j = min(j + chunk_size, len(embeddings_sample))
                        chunk_similarity = np.dot(embeddings_norm[i:end_i], embeddings_norm[j:end_j].T)
                        similarity_matrix[i:end_i, j:end_j] = chunk_similarity
                
                logger.info(f"✅ Matriz de similaridade calculada com sucesso")
                
            except MemoryError as e:
                logger.error(f"❌ Erro de memória ao calcular similaridade: {e}")
                logger.info("💡 Tentando método alternativo com amostragem menor...")
                
                # Fallback: usar apenas uma amostra muito pequena
                max_docs_fallback = min(100, total_docs)
                indices_fallback = random.sample(range(total_docs), max_docs_fallback)
                embeddings_fallback = embeddings[indices_fallback]
                documents_fallback = [documents[i] for i in indices_fallback]
                
                embeddings_norm_fallback = embeddings_fallback / np.linalg.norm(embeddings_fallback, axis=1, keepdims=True)
                similarity_matrix = np.dot(embeddings_norm_fallback, embeddings_norm_fallback.T)
                embeddings_sample = embeddings_fallback
                documents_sample = documents_fallback
                actual_n_samples = min(n_samples, max_docs_fallback)
                
                logger.info(f"✅ Usando amostra reduzida de {max_docs_fallback} documentos")
            
            # Encontrar documentos mais similares
            np.fill_diagonal(similarity_matrix, 0)  # Remover auto-similaridade
            
            analysis = {
                'similarity_matrix': similarity_matrix,
                'most_similar_pairs': [],
                'average_similarity': np.mean(similarity_matrix),
                'similarity_std': np.std(similarity_matrix),
                'total_documents_analyzed': len(embeddings_sample),
                'total_documents_original': total_docs,
                'memory_optimized': total_docs > max_documents
            }
            
            # Encontrar pares mais similares
            for i in range(min(actual_n_samples, len(documents_sample))):
                most_similar_idx = np.argmax(similarity_matrix[i])
                similarity_score = similarity_matrix[i][most_similar_idx]
                
                analysis['most_similar_pairs'].append({
                    'doc1': documents_sample[i][:100] + "..." if len(documents_sample[i]) > 100 else documents_sample[i],
                    'doc2': documents_sample[most_similar_idx][:100] + "..." if len(documents_sample[most_similar_idx]) > 100 else documents_sample[most_similar_idx],
                    'similarity': float(similarity_score)
                })
            
            logger.info(f"✅ Análise de similaridade concluída para '{collection_name}'")
            logger.info(f"   - Documentos analisados: {len(embeddings_sample)}/{total_docs}")
            logger.info(f"   - Similaridade média: {analysis['average_similarity']:.3f}")
            logger.info(f"   - Desvio padrão: {analysis['similarity_std']:.3f}")
            if analysis['memory_optimized']:
                logger.info(f"   - ⚡ Otimização de memória aplicada")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de similaridade: {e}")
            if "Unable to allocate" in str(e):
                logger.error("💡 DICA: Coleção muito grande para análise completa")
                logger.info("💡 Soluções:")
                logger.info("   1. Use opção 5 (Relatório Completo) que otimiza automaticamente")
                logger.info("   2. Reduza o número de documentos na coleção")
                logger.info("   3. Execute em um sistema com mais RAM")
            return None
    
    def create_similarity_heatmap(self, collection_name: str, analysis: Dict[str, Any]) -> go.Figure:
        """Cria heatmap da matriz de similaridade"""
        try:
            similarity_matrix = analysis['similarity_matrix']
            
            # Criar heatmap
            fig = go.Figure(data=go.Heatmap(
                z=similarity_matrix,
                colorscale='Viridis',
                zmid=0.5,
                colorbar=dict(title="Similaridade (Cosseno)")
            ))
            
            fig.update_layout(
                title=f"Matriz de Similaridade - {collection_name}",
                xaxis_title="Documento",
                yaxis_title="Documento",
                width=800,
                height=600
            )
            
            logger.info(f"✅ Heatmap de similaridade criado para '{collection_name}'")
            return fig
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar heatmap: {e}")
            return None
    
    def export_visualization(self, fig: go.Figure, filename: str, format: str = "html"):
        """Exporta visualização para arquivo"""
        try:
            if format.lower() == "html":
                fig.write_html(f"{filename}.html")
                logger.info(f"✅ Visualização exportada para: {filename}.html")
            elif format.lower() == "png":
                fig.write_image(f"{filename}.png")
                logger.info(f"✅ Visualização exportada para: {filename}.png")
            elif format.lower() == "pdf":
                fig.write_image(f"{filename}.pdf")
                logger.info(f"✅ Visualização exportada para: {filename}.pdf")
            else:
                logger.warning(f"⚠️ Formato não suportado: {format}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao exportar visualização: {e}")
    
    def generate_report(self, collection_name: str, output_dir: str = "visualizations"):
        """Gera relatório completo de visualizações"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            logger.info(f"📊 Gerando relatório completo para '{collection_name}'...")
            
            # 1. Visualização 3D com PCA
            fig_3d_pca = self.create_3d_scatter(collection_name, "pca")
            if fig_3d_pca:
                self.export_visualization(fig_3d_pca, output_path / f"{collection_name}_3d_pca")
            
            # 2. Visualização 3D com UMAP
            fig_3d_umap = self.create_3d_scatter(collection_name, "umap")
            if fig_3d_umap:
                self.export_visualization(fig_3d_umap, output_path / f"{collection_name}_3d_umap")
            
            # 3. Comparação 2D
            fig_2d = self.create_2d_visualizations(collection_name)
            if fig_2d:
                self.export_visualization(fig_2d, output_path / f"{collection_name}_2d_comparison")
            
            # 4. Análise de similaridade
            analysis = self.analyze_similarity(collection_name)
            if analysis:
                # Salvar dados de análise
                with open(output_path / f"{collection_name}_similarity_analysis.json", 'w', encoding='utf-8') as f:
                    json.dump({
                        'average_similarity': analysis['average_similarity'],
                        'similarity_std': analysis['similarity_std'],
                        'most_similar_pairs': analysis['most_similar_pairs']
                    }, f, indent=2, ensure_ascii=False)
                
                # Criar heatmap
                fig_heatmap = self.create_similarity_heatmap(collection_name, analysis)
                if fig_heatmap:
                    self.export_visualization(fig_heatmap, output_path / f"{collection_name}_similarity_heatmap")
            
            # 5. Relatório HTML
            self.create_html_report(collection_name, output_path, analysis)
            
            logger.info(f"✅ Relatório completo gerado em: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")
    
    def create_html_report(self, collection_name: str, output_path: Path, analysis: Dict[str, Any]):
        """Cria relatório HTML completo com explicações sobre métodos de redução de dimensionalidade"""
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Relatório de Visualização - {collection_name}</title>
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                    }}
                    
                    .container {{
                        max-width: 1400px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    
                    .header {{
                        text-align: center;
                        color: white;
                        margin-bottom: 40px;
                        padding: 30px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 20px;
                        backdrop-filter: blur(10px);
                    }}
                    
                    .header h1 {{
                        font-size: 2.5rem;
                        margin-bottom: 10px;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }}
                    
                    .header p {{
                        font-size: 1.2rem;
                        opacity: 0.9;
                    }}
                    
                    .nav-tabs {{
                        display: flex;
                        justify-content: center;
                        margin-bottom: 30px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 15px;
                        padding: 10px;
                        backdrop-filter: blur(10px);
                        flex-wrap: wrap;
                    }}
                    
                    .nav-tab {{
                        background: none;
                        border: none;
                        color: white;
                        padding: 15px 25px;
                        margin: 5px;
                        border-radius: 10px;
                        cursor: pointer;
                        font-size: 1rem;
                        font-weight: 500;
                        transition: all 0.3s ease;
                        white-space: nowrap;
                    }}
                    
                    .nav-tab:hover {{
                        background: rgba(255, 255, 255, 0.2);
                        transform: translateY(-2px);
                    }}
                    
                    .nav-tab.active {{
                        background: rgba(255, 255, 255, 0.3);
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    }}
                    
                    .content-section {{
                        background: white;
                        border-radius: 20px;
                        padding: 30px;
                        margin-bottom: 30px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                        display: none;
                    }}
                    
                    .content-section.active {{
                        display: block;
                        animation: fadeIn 0.5s ease-in;
                    }}
                    
                    @keyframes fadeIn {{
                        from {{ opacity: 0; transform: translateY(20px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                    
                    .method-card {{
                        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                        border-radius: 15px;
                        padding: 25px;
                        margin: 20px 0;
                        border-left: 5px solid #667eea;
                        transition: all 0.3s ease;
                    }}
                    
                    .method-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                    }}
                    
                    .method-title {{
                        color: #667eea;
                        font-size: 1.5rem;
                        margin-bottom: 15px;
                        font-weight: 600;
                    }}
                    
                    .method-explanation {{
                        font-size: 1.1rem;
                        line-height: 1.8;
                        margin-bottom: 20px;
                    }}
                    
                    .pros-cons {{
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 20px;
                        margin-top: 20px;
                    }}
                    
                    .pros, .cons {{
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        border: 2px solid;
                    }}
                    
                    .pros {{
                        border-color: #28a745;
                    }}
                    
                    .cons {{
                        border-color: #dc3545;
                    }}
                    
                    .pros h4, .cons h4 {{
                        margin-bottom: 15px;
                        font-size: 1.2rem;
                    }}
                    
                    .pros h4 {{
                        color: #28a745;
                    }}
                    
                    .cons h4 {{
                        color: #dc3545;
                    }}
                    
                    .pros ul, .cons ul {{
                        list-style: none;
                        padding-left: 0;
                    }}
                    
                    .pros li, .cons li {{
                        padding: 8px 0;
                        position: relative;
                        padding-left: 25px;
                    }}
                    
                    .pros li:before {{
                        content: "✅";
                        position: absolute;
                        left: 0;
                        color: #28a745;
                    }}
                    
                    .cons li:before {{
                        content: "❌";
                        position: absolute;
                        left: 0;
                        color: #dc3545;
                    }}
                    
                    .info-box {{
                        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                        border: 2px solid #2196f3;
                        border-radius: 15px;
                        padding: 20px;
                        margin: 20px 0;
                    }}
                    
                    .info-box h3 {{
                        color: #1976d2;
                        margin-bottom: 15px;
                    }}
                    
                    .comparison-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                        background: white;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    }}
                    
                    .comparison-table th, .comparison-table td {{
                        padding: 15px;
                        text-align: left;
                        border-bottom: 1px solid #e0e0e0;
                    }}
                    
                    .comparison-table th {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        font-weight: 600;
                    }}
                    
                    .comparison-table tr:hover {{
                        background: #f8f9fa;
                    }}
                    
                    .metrics-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin: 20px 0;
                    }}
                    
                    .metric {{
                        background: white;
                        padding: 20px;
                        border-radius: 15px;
                        text-align: center;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                        border: 2px solid rgba(255, 255, 255, 0.3);
                    }}
                    
                    .metric-value {{
                        font-size: 2rem;
                        font-weight: bold;
                        color: #667eea;
                        margin-bottom: 10px;
                    }}
                    
                    .metric-label {{
                        color: #666;
                        font-size: 0.9rem;
                    }}
                    
                    .visualization-section {{
                        background: white;
                        border-radius: 15px;
                        padding: 20px;
                        margin: 20px 0;
                        text-align: center;
                    }}
                    
                    .visualization-section iframe {{
                        width: 100%;
                        height: 600px;
                        border: none;
                        border-radius: 10px;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    }}
                    
                    .similarity-pair {{
                        background: white;
                        margin: 10px 0;
                        padding: 15px;
                        border-radius: 10px;
                        border-left: 4px solid #667eea;
                    }}
                    
                    .similarity-score {{
                        font-weight: bold;
                        color: #667eea;
                        font-size: 1.1rem;
                        margin-bottom: 10px;
                    }}
                    
                    .footer {{
                        text-align: center;
                        color: white;
                        margin-top: 40px;
                        padding: 20px;
                        opacity: 0.8;
                    }}
                    
                    @media (max-width: 768px) {{
                        .container {{
                            padding: 10px;
                        }}
                        
                        .header h1 {{
                            font-size: 2rem;
                        }}
                        
                        .nav-tabs {{
                            flex-direction: column;
                            align-items: center;
                        }}
                        
                        .nav-tab {{
                            margin: 5px 0;
                            width: 100%;
                            max-width: 300px;
                        }}
                        
                        .pros-cons {{
                            grid-template-columns: 1fr;
                        }}
                        
                        .metrics-grid {{
                            grid-template-columns: 1fr;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔍 Relatório de Visualização do Banco de Dados Vetorial</h1>
                        <h2>Coleção: {collection_name}</h2>
                        <p>Gerado em: {time.strftime('%d/%m/%Y %H:%M:%S')}</p>
                        <p>📚 Inclui explicações sobre métodos de redução de dimensionalidade</p>
                    </div>
                    
                    <div class="nav-tabs">
                        <button class="nav-tab active" onclick="showSection('overview')">📊 Visão Geral</button>
                        <button class="nav-tab" onclick="showSection('methods')">🔧 Métodos</button>
                        <button class="nav-tab" onclick="showSection('visualizations')">🎯 Visualizações</button>
                        <button class="nav-tab" onclick="showSection('similarity')">🔗 Similaridade</button>
                        <button class="nav-tab" onclick="showSection('comparison')">📈 Comparação</button>
                        <button class="nav-tab" onclick="showSection('importance')">🚀 Importância</button>
                    </div>
                    
                    <!-- Seção: Visão Geral -->
                    <div id="overview" class="content-section active">
                        <h2>📊 Métricas Gerais da Coleção</h2>
                        <div class="metrics-grid">
                            <div class="metric">
                                <div class="metric-value">{len(self.documents[collection_name])}</div>
                                <div class="metric-label">Total de Documentos</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">{self.embeddings[collection_name].shape[1]}</div>
                                <div class="metric-label">Dimensões dos Embeddings</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">{analysis['average_similarity']:.3f if analysis else 'N/A'}</div>
                                <div class="metric-label">Similaridade Média</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">{analysis['similarity_std']:.3f if analysis else 'N/A'}</div>
                                <div class="metric-label">Desvio Padrão</div>
                            </div>
                        </div>
                        
                        <div class="info-box">
                            <h3>💡 Sobre Esta Coleção</h3>
                            <p>
                                Esta coleção contém <strong>{len(self.documents[collection_name])}</strong> documentos, 
                                cada um representado por um vetor de <strong>{self.embeddings[collection_name].shape[1]}</strong> dimensões.
                                Para visualizar e analisar esses dados de alta dimensionalidade, usamos métodos de redução de dimensionalidade.
                            </p>
                        </div>
                    </div>
                    
                    <!-- Seção: Métodos de Redução -->
                    <div id="methods" class="content-section">
                        <h2>🔧 Métodos de Redução de Dimensionalidade</h2>
                        
                        <div class="method-card">
                            <h3 class="method-title">🔧 PCA (Análise de Componentes Principais)</h3>
                            <p class="method-explanation">
                                Imagine que você tem uma foto de um rosto em alta resolução (muitos pixels). 
                                PCA é como criar uma versão "resumida" dessa foto, mantendo apenas os detalhes mais importantes.
                            </p>
                            
                            <h4>🎯 O que faz</h4>
                            <ul>
                                <li>Pega os dados em muitas dimensões</li>
                                <li>Identifica as "direções" mais importantes (onde há mais variação)</li>
                                <li>Projeta tudo nessas direções principais</li>
                                <li>Resultado: 2D ou 3D que preserva a "essência" dos dados</li>
                            </ul>
                            
                            <div class="pros-cons">
                                <div class="pros">
                                    <h4>✅ Vantagens</h4>
                                    <ul>
                                        <li>Rápido e eficiente</li>
                                        <li>Preserva a estrutura global dos dados</li>
                                        <li>Bom para encontrar padrões gerais</li>
                                    </ul>
                                </div>
                                <div class="cons">
                                    <h4>❌ Limitações</h4>
                                    <ul>
                                        <li>Pode perder detalhes locais importantes</li>
                                        <li>Não é muito bom para encontrar grupos pequenos</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        
                        <div class="method-card">
                            <h3 class="method-title">🌌 UMAP (Uniform Manifold Approximation and Projection)</h3>
                            <p class="method-explanation">
                                Imagine que você tem um mapa de uma cidade com muitas ruas. UMAP é como criar um mapa simplificado 
                                que mostra os bairros principais e como eles se conectam, mantendo as distâncias relativas.
                            </p>
                            
                            <h4>🎯 O que faz</h4>
                            <ul>
                                <li>Preserva tanto a estrutura local quanto global</li>
                                <li>Cria uma "rede" que conecta pontos similares</li>
                                <li>Mantém as relações de proximidade entre documentos</li>
                            </ul>
                            
                            <div class="pros-cons">
                                <div class="pros">
                                    <h4>✅ Vantagens</h4>
                                    <ul>
                                        <li>Preserva melhor a estrutura local dos dados</li>
                                        <li>Excelente para encontrar clusters (grupos)</li>
                                        <li>Bom para visualização interativa</li>
                                        <li>Mais rápido que t-SNE</li>
                                    </ul>
                                </div>
                                <div class="cons">
                                    <h4>❌ Limitações</h4>
                                    <ul>
                                        <li>Pode ser menos estável que PCA</li>
                                        <li>Parâmetros podem afetar o resultado</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        
                        <div class="method-card">
                            <h3 class="method-title">🎯 T-SNE (T-Distributed Stochastic Neighbor Embedding)</h3>
                            <p class="method-explanation">
                                Imagine que você tem um grupo de pessoas em uma sala. T-SNE é como reorganizar essas pessoas 
                                em uma sala menor, colocando amigos próximos uns dos outros e estranhos mais distantes.
                            </p>
                            
                            <h4>🎯 O que faz</h4>
                            <ul>
                                <li>Foca na preservação de distâncias locais</li>
                                <li>Coloca documentos similares próximos</li>
                                <li>Separa bem grupos diferentes</li>
                            </ul>
                            
                            <div class="pros-cons">
                                <div class="pros">
                                    <h4>✅ Vantagens</h4>
                                    <ul>
                                        <li>Excelente para encontrar clusters</li>
                                        <li>Preserva muito bem a estrutura local</li>
                                        <li>Ótimo para visualizar grupos de documentos similares</li>
                                    </ul>
                                </div>
                                <div class="cons">
                                    <h4>❌ Limitações</h4>
                                    <ul>
                                        <li>Pode distorcer a estrutura global</li>
                                        <li>Mais lento que PCA e UMAP</li>
                                        <li>Resultado pode variar entre execuções</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Seção: Visualizações -->
                    <div id="visualizations" class="content-section">
                        <h2>🎯 Visualizações 3D e 2D</h2>
                        
                        <div class="visualization-section">
                            <h3>🎯 Visualização 3D - PCA</h3>
                            <p>Visualização tridimensional usando Análise de Componentes Principais</p>
                            <iframe src="{collection_name}_3d_pca.html"></iframe>
                        </div>
                        
                        <div class="visualization-section">
                            <h3>🌌 Visualização 3D - UMAP</h3>
                            <p>Visualização tridimensional usando UMAP para melhor preservação de estrutura</p>
                            <iframe src="{collection_name}_3d_umap.html"></iframe>
                        </div>
                        
                        <div class="visualization-section">
                            <h3>📈 Comparação de Métodos 2D</h3>
                            <p>Comparação entre PCA, t-SNE e UMAP em duas dimensões</p>
                            <iframe src="{collection_name}_2d_comparison.html"></iframe>
                        </div>
                    </div>
                    
                    <!-- Seção: Similaridade -->
                    <div id="similarity" class="content-section">
                        <h2>🔗 Análise de Similaridade</h2>
                        
                        <div class="visualization-section">
                            <h3>🔥 Matriz de Similaridade</h3>
                            <p>Heatmap mostrando a similaridade entre todos os documentos</p>
                            <iframe src="{collection_name}_similarity_heatmap.html"></iframe>
                        </div>
                        
                        <h3>🔗 Documentos Mais Similares</h3>
                        {self._generate_similarity_html(analysis) if analysis else '<p>Análise não disponível</p>'}
                    </div>
                    
                    <!-- Seção: Comparação -->
                    <div id="comparison" class="content-section">
                        <h2>📊 Comparação dos Métodos</h2>
                        <div class="method-card">
                            <table class="comparison-table">
                                <thead>
                                    <tr>
                                        <th>Método</th>
                                        <th>Velocidade</th>
                                        <th>Estrutura Global</th>
                                        <th>Estrutura Local</th>
                                        <th>Melhor Para</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>PCA</strong></td>
                                        <td>🚀 Muito Rápido</td>
                                        <td>✅ Excelente</td>
                                        <td>⚠️ Limitada</td>
                                        <td>Visão geral, análise inicial</td>
                                    </tr>
                                    <tr>
                                        <td><strong>UMAP</strong></td>
                                        <td>⚡ Rápido</td>
                                        <td>✅ Boa</td>
                                        <td>✅ Excelente</td>
                                        <td>Análise detalhada, interativa</td>
                                    </tr>
                                    <tr>
                                        <td><strong>T-SNE</strong></td>
                                        <td>🐌 Lento</td>
                                        <td>❌ Limitada</td>
                                        <td>✅ Excelente</td>
                                        <td>Encontrar grupos específicos</td>
                                    </tr>
                                </tbody>
                            </table>
                            
                            <div class="info-box">
                                <h3>💡 Recomendações de Uso</h3>
                                <ul>
                                    <li><strong>PCA:</strong> Para visão geral e análise inicial</li>
                                    <li><strong>UMAP:</strong> Para análise detalhada e interativa</li>
                                    <li><strong>T-SNE:</strong> Para encontrar grupos específicos</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Seção: Importância -->
                    <div id="importance" class="content-section">
                        <h2>🚀 Importância no Banco de Dados Vetorial</h2>
                        <div class="method-card">
                            <h3>💡 Por que isso é crítico?</h3>
                            
                            <div class="info-box">
                                <h4>1. Visualização Humana</h4>
                                <p>Humanos só conseguem ver 2D/3D. Sem redução, é impossível "ver" os dados.</p>
                            </div>
                            
                            <div class="info-box">
                                <h4>2. Análise de Clusters</h4>
                                <p>Documentos similares ficam próximos. Fácil identificar grupos de conteúdo relacionado.</p>
                            </div>
                            
                            <div class="info-box">
                                <h4>3. Qualidade dos Dados</h4>
                                <p>Revela se os embeddings estão funcionando bem. Mostra se documentos similares estão realmente próximos.</p>
                            </div>
                            
                            <div class="info-box">
                                <h4>4. Debugging do Sistema</h4>
                                <p>Identifica problemas na indexação. Mostra se o banco está organizado corretamente.</p>
                            </div>
                            
                            <div class="info-box">
                                <h4>5. Otimização</h4>
                                <p>Ajuda a ajustar parâmetros do sistema. Mostra onde melhorar a qualidade dos embeddings.</p>
                            </div>
                            
                            <h3>🎨 Como Interpretar os Resultados</h3>
                            
                            <div class="pros">
                                <h4>✅ Grupos Bem Definidos</h4>
                                <ul>
                                    <li>Documentos similares estão próximos</li>
                                    <li>Clusters claros e separados</li>
                                    <li>Sistema funcionando bem</li>
                                </ul>
                            </div>
                            
                            <div class="cons">
                                <h4>⚠️ Grupos Difusos</h4>
                                <ul>
                                    <li>Documentos similares espalhados</li>
                                    <li>Clusters mal definidos</li>
                                    <li>Possível problema nos embeddings</li>
                                </ul>
                            </div>
                            
                            <div class="info-box">
                                <h3>💡 Dica Importante</h3>
                                <p>
                                    Esses métodos não "criam" informação - eles apenas reorganizam o que já existe. 
                                    Se seus documentos não estão bem organizados no espaço vetorial original, 
                                    a redução de dimensionalidade não vai "consertar" isso!
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>🔍 Sistema RAG DNA da Força - Relatório de Visualização com Explicações</p>
                        <p>💡 Use essas explicações para entender melhor seu banco de dados vetorial</p>
                        <p>📅 Gerado em: {time.strftime('%d/%m/%Y %H:%M:%S')}</p>
                    </div>
                </div>
                
                <script>
                    function showSection(sectionId) {{
                        // Esconder todas as seções
                        const sections = document.querySelectorAll('.content-section');
                        sections.forEach(section => {{
                            section.classList.remove('active');
                        }});
                        
                        // Remover classe active de todas as tabs
                        const tabs = document.querySelectorAll('.nav-tab');
                        tabs.forEach(tab => {{
                            tab.classList.remove('active');
                        }});
                        
                        // Mostrar seção selecionada
                        document.getElementById(sectionId).classList.add('active');
                        
                        // Adicionar classe active na tab clicada
                        event.target.classList.add('active');
                    }}
                    
                    // Adicionar efeitos de hover e animações
                    document.addEventListener('DOMContentLoaded', function() {{
                        const methodCards = document.querySelectorAll('.method-card');
                        methodCards.forEach(card => {{
                            card.addEventListener('mouseenter', function() {{
                                this.style.transform = 'translateY(-5px)';
                            }});
                            
                            card.addEventListener('mouseleave', function() {{
                                this.style.transform = 'translateY(0)';
                            }});
                        }});
                    }});
                </script>
            </body>
            </html>
            """
            
            with open(output_path / f"{collection_name}_report.html", 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ Relatório HTML criado: {output_path / f'{collection_name}_report.html'}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar relatório HTML: {e}")
    
    def _generate_similarity_html(self, analysis: Dict[str, Any]) -> str:
        """Gera HTML para pares similares com novo estilo"""
        html = ""
        for pair in analysis['most_similar_pairs'][:10]:  # Top 10
            html += f"""
            <div class="similarity-pair">
                <div class="similarity-score">Similaridade: {pair['similarity']:.3f}</div>
                <div><strong>📄 Doc 1:</strong> {pair['doc1']}</div>
                <div><strong>📄 Doc 2:</strong> {pair['doc2']}</div>
            </div>
            """
        return html


def get_user_input(prompt: str, valid_options: List[str] = None, input_type: str = "text") -> Any:
    """Função auxiliar para obter entrada do usuário com validação"""
    while True:
        try:
            if input_type == "int":
                user_input = int(input(prompt))
                if valid_options and user_input not in valid_options:
                    print(f"❌ Por favor, escolha uma opção válida: {valid_options}")
                    continue
                return user_input
            elif input_type == "float":
                return float(input(prompt))
            elif input_type == "bool":
                user_input = input(prompt).lower().strip()
                if user_input in ['s', 'sim', 'y', 'yes', 'true', '1']:
                    return True
                elif user_input in ['n', 'não', 'nao', 'no', 'false', '0']:
                    return False
                else:
                    print("❌ Por favor, responda com 's' (sim) ou 'n' (não)")
                    continue
            else:
                user_input = input(prompt).strip()
                if not user_input:
                    print("❌ Por favor, digite algo válido")
                    continue
                return user_input
        except ValueError:
            print("❌ Entrada inválida. Tente novamente.")
        except KeyboardInterrupt:
            print("\n👋 Interrompido pelo usuário")
            sys.exit(0)


def main():
    """Função principal para executar o visualizador"""
    print("🔍 Visualizador 3D do Banco de Dados Vetorial")
    print("=" * 60)
    print("📖 Este programa permite visualizar e analisar o banco de dados vetorial")
    print("   do sistema RAG em 3D, incluindo clustering e análise de similaridade.")
    print()
    
    # Inicializar visualizador
    visualizer = VectorDBVisualizer()
    
    # Conectar ao ChromaDB
    print("🔌 Conectando ao banco de dados vetorial...")
    if not visualizer.connect_to_chromadb():
        print("❌ Falha ao conectar ao ChromaDB")
        print("💡 Verifique se o diretório 'data/.chromadb' existe e contém dados válidos")
        return
    
    # Listar coleções disponíveis
    collections = visualizer.client.list_collections()
    if not collections:
        print("❌ Nenhuma coleção encontrada no banco de dados")
        print("💡 O banco de dados pode estar vazio ou não foi inicializado corretamente")
        return
    
    print(f"\n📚 Coleções disponíveis no banco de dados:")
    for i, collection in enumerate(collections):
        doc_count = collection.count()
        print(f"   {i+1}. {collection.name} ({doc_count} documentos)")
    
    # Selecionar coleção com validação
    print(f"\n🎯 Selecione uma coleção para visualizar:")
    print("   💡 Digite o número da coleção desejada")
    
    try:
        choice = get_user_input(
            f"   Escolha (1-{len(collections)}): ", 
            list(range(1, len(collections) + 1)), 
            "int"
        )
        
        selected_collection = collections[choice - 1].name
        print(f"✅ Coleção selecionada: {selected_collection}")
        
    except (ValueError, IndexError):
        print("❌ Escolha inválida")
        return
    
    # Carregar dados da coleção
    print(f"\n📥 Carregando dados da coleção '{selected_collection}'...")
    if not visualizer.load_collection_data(selected_collection):
        print("❌ Falha ao carregar dados da coleção")
        return
    
    print(f"✅ Dados carregados com sucesso!")
    print(f"   📊 Total de documentos: {len(visualizer.documents[selected_collection])}")
    print(f"   🧠 Dimensões dos embeddings: {visualizer.embeddings[selected_collection].shape[1]}")
    
    # Menu principal de opções
    while True:
        print(f"\n🔧 Menu de Visualizações - {selected_collection}")
        print("=" * 50)
        print("1. 🎯 Visualização 3D (PCA)")
        print("   💡 Mostra documentos em 3D usando Análise de Componentes Principais")
        print("   📊 Inclui clustering automático dos documentos")
        print()
        print("2. 🌌 Visualização 3D (UMAP)")
        print("   💡 Visualização 3D usando UMAP para melhor preservação de estrutura")
        print("   🎨 Ideal para análise de clusters e relacionamentos")
        print()
        print("3. 📈 Comparação 2D (PCA, t-SNE, UMAP)")
        print("   💡 Compara diferentes métodos de redução de dimensionalidade")
        print("   🔍 Útil para escolher o melhor método para seus dados")
        print()
        print("4. 🔗 Análise de Similaridade")
        print("   💡 Analisa como os documentos se relacionam entre si")
        print("   📊 Inclui matriz de similaridade e pares mais similares")
        print()
        print("5. 📊 Gerar Relatório Completo")
        print("   💡 Cria todas as visualizações e salva em arquivos")
        print("   📁 Salva em HTML, PNG e PDF para uso posterior")
        print()
        print("6. 🚪 Sair")
        print("   💡 Encerra o programa")
        print()
        
        try:
            option = get_user_input("🎯 Escolha uma opção (1-6): ", list(range(1, 7)), "int")
            
            if option == 1:
                print(f"\n🎯 Criando visualização 3D com PCA...")
                print("   💡 PCA preserva a variância máxima dos dados")
                print("   ⏳ Isso pode levar alguns segundos para coleções grandes...")
                
                fig = visualizer.create_3d_scatter(selected_collection, "pca")
                if fig:
                    print("✅ Visualização 3D criada com sucesso!")
                    print("   🖱️ Use o mouse para rotacionar, zoom e pan")
                    print("   📱 Toque e arraste em dispositivos touch")
                    fig.show()
                    
                    save = get_user_input("💾 Salvar visualização? (s/n): ", input_type="bool")
                    if save:
                        filename = get_user_input("📝 Nome do arquivo (sem extensão): ")
                        if filename:
                            visualizer.export_visualization(fig, filename, "html")
                            print(f"✅ Visualização salva como: {filename}.html")
                else:
                    print("❌ Falha ao criar visualização 3D")
            
            elif option == 2:
                print(f"\n🌌 Criando visualização 3D com UMAP...")
                print("   💡 UMAP preserva melhor a estrutura local dos dados")
                print("   ⏳ Processando... (pode demorar para coleções grandes)")
                
                fig = visualizer.create_3d_scatter(selected_collection, "umap")
                if fig:
                    print("✅ Visualização 3D UMAP criada com sucesso!")
                    print("   🖱️ Use o mouse para rotacionar, zoom e pan")
                    print("   📱 Toque e arraste em dispositivos touch")
                    fig.show()
                    
                    save = get_user_input("💾 Salvar visualização? (s/n): ", input_type="bool")
                    if save:
                        filename = get_user_input("📝 Nome do arquivo (sem extensão): ")
                        if filename:
                            visualizer.export_visualization(fig, filename, "html")
                            print(f"✅ Visualização salva como: {filename}.html")
                else:
                    print("❌ Falha ao criar visualização 3D UMAP")
            
            elif option == 3:
                print(f"\n📈 Criando comparação de métodos 2D...")
                print("   💡 Comparando PCA, t-SNE e UMAP para 2 dimensões")
                print("   ⏳ Processando... (pode demorar para coleções grandes)")
                
                fig = visualizer.create_2d_visualizations(selected_collection)
                if fig:
                    print("✅ Comparação 2D criada com sucesso!")
                    print("   📊 PCA: Preserva variância global")
                    print("   🎯 t-SNE: Foca em estrutura local")
                    print("   🌌 UMAP: Equilibra local e global")
                    fig.show()
                    
                    save = get_user_input("💾 Salvar comparação? (s/n): ", input_type="bool")
                    if save:
                        filename = get_user_input("📝 Nome do arquivo (sem extensão): ")
                        if filename:
                            visualizer.export_visualization(fig, filename, "html")
                            print(f"✅ Comparação salva como: {filename}.html")
                else:
                    print("❌ Falha ao criar comparação 2D")
            
            elif option == 4:
                print(f"\n🔗 Analisando similaridade entre documentos...")
                print("   💡 Calculando matriz de similaridade usando cosseno")
                print("   ⏳ Processando...")
                
                analysis = visualizer.analyze_similarity(selected_collection)
                if analysis:
                    print("✅ Análise de similaridade concluída!")
                    print(f"\n📊 Métricas de Similaridade:")
                    print(f"   - Média: {analysis['average_similarity']:.3f}")
                    print(f"   - Desvio Padrão: {analysis['similarity_std']:.3f}")
                    
                    print(f"\n🔗 Top 5 Pares Mais Similares:")
                    for i, pair in enumerate(analysis['most_similar_pairs'][:5]):
                        print(f"   {i+1}. Similaridade: {pair['similarity']:.3f}")
                        print(f"      📄 Doc 1: {pair['doc1'][:80]}...")
                        print(f"      📄 Doc 2: {pair['doc2'][:80]}...")
                        print()
                    
                    # Criar e mostrar heatmap
                    print("🔥 Criando heatmap de similaridade...")
                    fig = visualizer.create_similarity_heatmap(selected_collection, analysis)
                    if fig:
                        print("✅ Heatmap criado com sucesso!")
                        print("   🔥 Cores mais quentes = maior similaridade")
                        print("   ❄️ Cores mais frias = menor similaridade")
                        fig.show()
                        
                        save = get_user_input("💾 Salvar heatmap? (s/n): ", input_type="bool")
                        if save:
                            filename = get_user_input("📝 Nome do arquivo (sem extensão): ")
                            if filename:
                                visualizer.export_visualization(fig, filename, "html")
                                print(f"✅ Heatmap salvo como: {filename}.html")
                    else:
                        print("❌ Falha ao criar heatmap")
                else:
                    print("❌ Falha na análise de similaridade")
            
            elif option == 5:
                print(f"\n📊 Gerando relatório completo...")
                print("   💡 Criando todas as visualizações disponíveis")
                print("   📁 Salvando em pasta 'visualizations'")
                print("   ⏳ Isso pode levar alguns minutos...")
                
                try:
                    visualizer.generate_report(selected_collection)
                    print("✅ Relatório completo gerado com sucesso!")
                    print("   📁 Pasta: visualizations/")
                    print("   📄 Arquivo principal: visualizations/{selected_collection}_report.html")
                    print("   🎯 Abra o arquivo HTML no seu navegador para ver tudo")
                except Exception as e:
                    print(f"❌ Erro ao gerar relatório: {e}")
            
            elif option == 6:
                print("\n📚 Explicando Métodos de Redução de Dimensionalidade...")
                print("=" * 60)
                
                explanation = """
🔍 **O QUE SÃO ESSES MÉTODOS E POR QUE SÃO IMPORTANTES?**

📚 **CONTEXTO: O PROBLEMA DOS DADOS VETORIAIS**

Imagine que cada documento do seu banco de dados é como um ponto no espaço, mas não um espaço normal de 3 dimensões (altura, largura, profundidade). 
É um espaço de MUITAS dimensões - pode ter 1536, 4096 ou até mais dimensões!

💡 **POR QUE ISSO É UM PROBLEMA?**
- Humanos só conseguem visualizar 2D ou 3D
- Computadores têm dificuldade com tantas dimensões
- É como tentar entender um cubo de 1536 dimensões!

🎯 **SOLUÇÃO: REDUÇÃO DE DIMENSIONALIDADE**

Os métodos PCA, UMAP e t-SNE são como "tradutores" que pegam esses pontos em muitas dimensões 
e os colocam em 2D ou 3D, mantendo o máximo possível de informação importante.

---

🔧 **PCA (ANÁLISE DE COMPONENTES PRINCIPAIS)**

💭 **EXPLICAÇÃO SIMPLES:**
Imagine que você tem uma foto de um rosto em alta resolução (muitos pixels). 
PCA é como criar uma versão "resumida" dessa foto, mantendo apenas os detalhes mais importantes.

🎯 **O QUE FAZ:**
- Pega os dados em muitas dimensões
- Identifica as "direções" mais importantes (onde há mais variação)
- Projeta tudo nessas direções principais
- Resultado: 2D ou 3D que preserva a "essência" dos dados

✅ **VANTAGENS:**
- Rápido e eficiente
- Preserva a estrutura global dos dados
- Bom para encontrar padrões gerais

❌ **LIMITAÇÕES:**
- Pode perder detalhes locais importantes
- Não é muito bom para encontrar grupos pequenos

---

🌌 **UMAP (UNIFORM MANIFOLD APPROXIMATION AND PROJECTION)**

💭 **EXPLICAÇÃO SIMPLES:**
Imagine que você tem um mapa de uma cidade com muitas ruas. UMAP é como criar um mapa simplificado 
que mostra os bairros principais e como eles se conectam, mantendo as distâncias relativas.

🎯 **O QUE FAZ:**
- Preserva tanto a estrutura local quanto global
- Cria uma "rede" que conecta pontos similares
- Mantém as relações de proximidade entre documentos

✅ **VANTAGENS:**
- Preserva melhor a estrutura local dos dados
- Excelente para encontrar clusters (grupos)
- Bom para visualização interativa
- Mais rápido que t-SNE

❌ **LIMITAÇÕES:**
- Pode ser menos estável que PCA
- Parâmetros podem afetar o resultado

---

🎯 **T-SNE (T-DISTRIBUTED STOCHASTIC NEIGHBOR EMBEDDING)**

💭 **EXPLICAÇÃO SIMPLES:**
Imagine que você tem um grupo de pessoas em uma sala. T-SNE é como reorganizar essas pessoas 
em uma sala menor, colocando amigos próximos uns dos outros e estranhos mais distantes.

🎯 **O QUE FAZ:**
- Foca na preservação de distâncias locais
- Coloca documentos similares próximos
- Separa bem grupos diferentes

✅ **VANTAGENS:**
- Excelente para encontrar clusters
- Preserva muito bem a estrutura local
- Ótimo para visualizar grupos de documentos similares

❌ **LIMITAÇÕES:**
- Pode distorcer a estrutura global
- Mais lento que PCA e UMAP
- Resultado pode variar entre execuções

---

🚀 **IMPORTÂNCIA NO BANCO DE DADOS VETORIAL**

💡 **POR QUE ISSO É CRÍTICO?**

1. **VISUALIZAÇÃO HUMANA:**
   - Humanos só conseguem ver 2D/3D
   - Sem redução, é impossível "ver" os dados

2. **ANÁLISE DE CLUSTERS:**
   - Documentos similares ficam próximos
   - Fácil identificar grupos de conteúdo relacionado

3. **QUALIDADE DOS DADOS:**
   - Revela se os embeddings estão funcionando bem
   - Mostra se documentos similares estão realmente próximos

4. **DEBUGGING DO SISTEMA:**
   - Identifica problemas na indexação
   - Mostra se o banco está organizado corretamente

5. **OTIMIZAÇÃO:**
   - Ajuda a ajustar parâmetros do sistema
   - Mostra onde melhorar a qualidade dos embeddings

---

🎨 **COMO INTERPRETAR OS RESULTADOS**

🔍 **GRUPOS BEM DEFINIDOS:**
- Documentos similares estão próximos
- Clusters claros e separados
- Sistema funcionando bem

⚠️ **GRUPOS DIFUSOS:**
- Documentos similares espalhados
- Clusters mal definidos
- Possível problema nos embeddings

🎯 **RECOMENDAÇÕES DE USO:**

- **PCA:** Para visão geral e análise inicial
- **UMAP:** Para análise detalhada e interativa
- **T-SNE:** Para encontrar grupos específicos

---

💡 **DICA IMPORTANTE:**
Esses métodos não "criam" informação - eles apenas reorganizam o que já existe. 
Se seus documentos não estão bem organizados no espaço vetorial original, 
a redução de dimensionalidade não vai "consertar" isso!

---

🎯 **NO SEU CASO ESPECÍFICO:**

Você tem uma coleção com {doc_count} documentos, cada um representado por um vetor de {embedding_dims} dimensões.

Isso significa que:
- Cada documento é um ponto em um espaço de {embedding_dims} dimensões
- É impossível "ver" essa estrutura sem redução de dimensionalidade
- Os métodos PCA, UMAP e t-SNE vão te permitir "ver" como seus documentos se organizam
- Você poderá identificar se documentos sobre o mesmo tema estão realmente próximos
- Poderá ver se há problemas na organização do seu banco vetorial

---

🚀 **PRÓXIMOS PASSOS:**

1. **Teste PCA primeiro** (opção 1) - para visão geral
2. **Teste UMAP** (opção 2) - para análise detalhada
3. **Compare os métodos** (opção 3) - para entender as diferenças
4. **Analise similaridade** (opção 4) - para ver relacionamentos
5. **Gere relatório completo** (opção 5) - para ter tudo salvo
                """.format(
                    doc_count=len(visualizer.documents[selected_collection]),
                    embedding_dims=visualizer.embeddings[selected_collection].shape[1]
                )
                
                # Mostrar explicação em partes para facilitar leitura
                lines = explanation.strip().split('\n')
                for line in lines:
                    if line.strip():
                        print(line)
                    else:
                        print()
                    
                    # Pausa para facilitar leitura
                    if line.startswith('---'):
                        input("\n⏸️ Pressione ENTER para continuar...")
                
                print("\n✅ Explicação concluída!")
                print("💡 Agora você entende por que esses métodos são importantes!")
                print("🎯 Use as opções 1-5 para explorar seu banco de dados vetorial")
            
            elif option == 7:
                print("\n👋 Encerrando o visualizador...")
                print("   💡 Obrigado por usar o sistema de visualização!")
                print("   📁 Lembre-se de verificar a pasta 'visualizations' para os arquivos salvos")
                break
            
            else:
                print("❌ Opção inválida. Por favor, escolha de 1 a 6.")
                
        except ValueError as e:
            print(f"❌ Erro de entrada: {e}")
        except KeyboardInterrupt:
            print("\n👋 Interrompido pelo usuário")
            break
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            print("💡 Tente novamente ou escolha outra opção")


if __name__ == "__main__":
    main()
