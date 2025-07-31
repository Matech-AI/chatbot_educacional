#!/usr/bin/env python3
"""
Script para testar a funcionalidade de download recursivo do Google Drive
Pasta alvo: https://drive.google.com/drive/folders/1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ

Este script testa o download recursivo completo da estrutura de pastas.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from drive_handler_recursive import RecursiveDriveHandler

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('recursive_drive_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_recursive_download():
    """Test recursive download functionality"""
    logger.info("🚀 Iniciando teste de download recursivo do Google Drive")
    logger.info("=" * 80)
    
    # Target folder ID from the URL provided
    ROOT_FOLDER_ID = "1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ"
    logger.info(f"🎯 Pasta raiz: {ROOT_FOLDER_ID}")
    logger.info(f"🔗 URL: https://drive.google.com/drive/folders/{ROOT_FOLDER_ID}")
    
    # Initialize Recursive Drive Handler
    logger.info("🔧 Inicializando RecursiveDriveHandler...")
    drive_handler = RecursiveDriveHandler()
    
    # Test authentication
    logger.info("🔐 Testando autenticação...")
    
    # Try different authentication methods
    auth_success = False
    
    # Method 1: Environment API key
    env_api_key = os.getenv('GOOGLE_DRIVE_API_KEY')
    if env_api_key:
        logger.info("🔑 Tentando com API Key do ambiente...")
        if drive_handler.authenticate(api_key=env_api_key):
            auth_success = True
            logger.info("✅ Autenticação com API Key bem-sucedida")
    
    # Method 2: OAuth2 credentials
    if not auth_success and os.path.exists('credentials.json'):
        logger.info("📄 Tentando com credentials.json...")
        if drive_handler.authenticate():
            auth_success = True
            logger.info("✅ Autenticação OAuth2 bem-sucedida")
    
    # Method 3: Public access
    if not auth_success:
        logger.info("🔓 Tentando acesso público...")
        if drive_handler.authenticate():
            auth_success = True
            logger.info("✅ Acesso público bem-sucedido")
    
    if not auth_success:
        logger.error("❌ Falha em todos os métodos de autenticação")
        return False
    
    logger.info("-" * 80)
    
    # Step 1: Analyze folder structure
    logger.info("📊 ETAPA 1: Analisando estrutura da pasta...")
    start_analysis = time.time()
    
    try:
        folder_structure = drive_handler.get_folder_structure(ROOT_FOLDER_ID)
        analysis_time = time.time() - start_analysis
        
        logger.info(f"✅ Análise concluída em {analysis_time:.2f}s")
        logger.info(f"📊 Estatísticas da análise:")
        logger.info(f"   - Total de pastas: {drive_handler.download_stats['total_folders']}")
        logger.info(f"   - Total de arquivos: {drive_handler.download_stats['total_files']}")
        logger.info(f"   - Pasta raiz: {folder_structure.get('name', 'Desconhecida')}")
        
        # Display folder structure
        print_folder_structure(folder_structure, 0)
        
    except Exception as e:
        logger.error(f"❌ Erro na análise da estrutura: {str(e)}")
        return False
    
    logger.info("-" * 80)
    
    # Ask user if they want to proceed with download
    total_files = drive_handler.download_stats['total_files']
    total_folders = drive_handler.download_stats['total_folders']
    
    print(f"\n📋 RESUMO DA ANÁLISE:")
    print(f"   📁 Pastas encontradas: {total_folders}")
    print(f"   📄 Arquivos encontrados: {total_files}")
    print(f"   📍 Pasta raiz: {folder_structure.get('name', 'Desconhecida')}")
    
    if total_files == 0:
        logger.warning("⚠️ Nenhum arquivo encontrado para download")
        return True
    
    response = input(f"\n❓ Deseja fazer o download recursivo de {total_files} arquivos? (s/N): ").strip().lower()
    
    if response not in ['s', 'sim', 'y', 'yes']:
        logger.info("ℹ️ Download cancelado pelo usuário")
        return True
    
    # Step 2: Recursive download
    logger.info("📥 ETAPA 2: Iniciando download recursivo...")
    start_download = time.time()
    
    try:
        result = drive_handler.download_drive_recursive(ROOT_FOLDER_ID)
        download_time = time.time() - start_download
        
        if result['status'] == 'success':
            logger.info("🎉 DOWNLOAD RECURSIVO CONCLUÍDO COM SUCESSO!")
            
            # Display detailed statistics
            stats = result['statistics']
            timing = result['timing']
            
            print(f"\n📊 ESTATÍSTICAS FINAIS:")
            print(f"   📁 Total de pastas: {stats['total_folders']}")
            print(f"   📄 Total de arquivos encontrados: {stats['total_files']}")
            print(f"   ✅ Arquivos baixados: {stats['downloaded_files']}")
            print(f"   ⏭️ Duplicatas ignoradas: {stats['skipped_duplicates']}")
            print(f"   ❌ Erros: {stats['errors']}")
            
            print(f"\n⏱️ TEMPOS:")
            print(f"   📊 Análise: {timing['analysis_time']:.2f}s")
            print(f"   📥 Download: {timing['download_time']:.2f}s")
            print(f"   🕐 Total: {timing['total_time']:.2f}s")
            
            # Show download efficiency
            if timing['total_time'] > 0:
                files_per_second = stats['downloaded_files'] / timing['total_time']
                print(f"   📈 Velocidade: {files_per_second:.2f} arquivos/s")
            
            # Show final folder structure
            final_stats = drive_handler.get_download_stats()
            print(f"\n📁 ESTRUTURA LOCAL CRIADA:")
            print(f"   📍 Diretório: {final_stats['directory']}")
            print(f"   📄 Total de arquivos salvos: {final_stats['total_files']}")
            print(f"   💾 Tamanho total: {format_bytes(final_stats['total_size'])}")
            
            # Show file types
            if final_stats['file_types']:
                print(f"   📋 Tipos de arquivo:")
                for ext, count in final_stats['file_types'].items():
                    ext_name = ext if ext else 'sem extensão'
                    print(f"      {ext_name}: {count} arquivos")
            
            # Show some downloaded files as examples
            processed_files = result['processed_files']
            if processed_files:
                print(f"\n📄 EXEMPLOS DE ARQUIVOS BAIXADOS:")
                for i, file in enumerate(processed_files[:10]):  # Show first 10
                    relative_path = file.get('relative_path', file.get('name', 'Unknown'))
                    size = format_bytes(file.get('size', 0))
                    print(f"   {i+1:2d}. {relative_path} ({size})")
                
                if len(processed_files) > 10:
                    print(f"   ... e mais {len(processed_files) - 10} arquivos")
            
            return True
            
        else:
            logger.error(f"❌ Erro no download recursivo: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro durante o download: {str(e)}")
        return False

def print_folder_structure(structure, level=0, max_level=3):
    """Print folder structure in a tree format"""
    if level > max_level:
        return
    
    indent = "  " * level
    folder_icon = "📁" if level == 0 else "📂"
    
    name = structure.get('name', 'Unknown')
    file_count = len(structure.get('files', []))
    subfolder_count = len(structure.get('subfolders', {}))
    
    print(f"{indent}{folder_icon} {name} ({file_count} arquivos, {subfolder_count} subpastas)")
    
    # Show first few files
    files = structure.get('files', [])
    for i, file in enumerate(files[:3]):  # Show first 3 files
        file_name = file.get('name', 'Unknown')
        print(f"{indent}  📄 {file_name}")
    
    if len(files) > 3:
        print(f"{indent}  📄 ... e mais {len(files) - 3} arquivos")
    
    # Show subfolders
    subfolders = structure.get('subfolders', {})
    for subfolder in list(subfolders.values())[:5]:  # Show first 5 subfolders
        print_folder_structure(subfolder, level + 1, max_level)
    
    if len(subfolders) > 5:
        print(f"{indent}  📂 ... e mais {len(subfolders) - 5} subpastas")

def format_bytes(bytes_size):
    """Format bytes to human readable format"""
    if bytes_size == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    
    return f"{bytes_size:.1f} TB"

def show_setup_instructions():
    """Show setup instructions"""
    print("\n" + "="*80)
    print("📖 INSTRUÇÕES DE CONFIGURAÇÃO PARA DOWNLOAD RECURSIVO")
    print("="*80)
    
    print("\n🔑 CONFIGURAÇÃO DA API (Escolha uma opção):")
    print("\n1️⃣ OPÇÃO 1: API Key (Recomendada para pastas públicas)")
    print("   • Vá para https://console.cloud.google.com/")
    print("   • Ative a Google Drive API")
    print("   • Crie uma API Key")
    print("   • Execute: export GOOGLE_DRIVE_API_KEY=sua_api_key")
    
    print("\n2️⃣ OPÇÃO 2: OAuth2 (Para pastas privadas)")
    print("   • Crie um OAuth2 Client ID no Google Cloud Console")
    print("   • Baixe as credenciais como 'credentials.json'")
    print("   • Coloque o arquivo na pasta do projeto")
    
    print("\n📁 PASTA DE TESTE:")
    print("   • URL: https://drive.google.com/drive/folders/1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ")
    print("   • Verifique se a pasta é pública ou configure as credenciais")
    
    print("\n🚀 EXECUTAR:")
    print("   python test_recursive_drive.py")
    
    print("\n⚡ RECURSOS DO DOWNLOAD RECURSIVO:")
    print("   ✅ Navega automaticamente por todas as subpastas")
    print("   ✅ Mantém a estrutura hierárquica localmente")
    print("   ✅ Detecta e evita duplicatas por conteúdo (SHA256)")
    print("   ✅ Relatórios detalhados de progresso e estatísticas")
    print("   ✅ Análise prévia sem download")
    print("   ✅ Tratamento robusto de erros")

def main():
    """Main function"""
    print("🚀 DNA da Força - Teste de Download Recursivo do Google Drive")
    print("="*80)
    
    # Check if we should show instructions
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_setup_instructions()
        return
    
    # Check basic setup
    logger.info("🔍 Verificando configuração...")
    
    has_api_key = bool(os.getenv('GOOGLE_DRIVE_API_KEY'))
    has_credentials = os.path.exists('credentials.json')
    
    print(f"📊 Status da configuração:")
    print(f"   🔑 API Key: {'✅' if has_api_key else '❌'}")
    print(f"   📄 Credentials: {'✅' if has_credentials else '❌'}")
    
    if not has_api_key and not has_credentials:
        print("\n⚠️ ATENÇÃO: Nenhuma credencial configurada!")
        print("O teste tentará acesso público, mas pode falhar.")
        print("Execute 'python test_recursive_drive.py --help' para instruções.")
    
    print("\n" + "="*80)
    response = input("❓ Deseja executar o teste de download recursivo agora? (s/N): ").strip().lower()
    
    if response in ['s', 'sim', 'y', 'yes']:
        try:
            success = test_recursive_download()
            if success:
                print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
                print("📁 Verifique a pasta 'data/materials' para os arquivos baixados.")
            else:
                print("\n❌ TESTE FALHOU!")
                print("📝 Verifique os logs em 'recursive_drive_test.log' para detalhes.")
        except KeyboardInterrupt:
            print("\n⏹️ Teste interrompido pelo usuário.")
        except Exception as e:
            print(f"\n💥 Erro inesperado: {str(e)}")
            logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
    else:
        print("ℹ️ Teste cancelado.")
        print("💡 Execute novamente quando estiver pronto ou use --help para instruções.")

if __name__ == "__main__":
    main()
