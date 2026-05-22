#!/usr/bin/env python3
"""
Script para testar conexão específica com Google Drive
Pasta alvo: https://drive.google.com/drive/folders/1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ

Este script testa diferentes métodos de autenticação e acesso à pasta específica.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add current directory to path so we can import our modules
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from drive_handler import DriveHandler

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('drive_test.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main test function"""
    logger.info("🚀 Iniciando teste de conexão com Google Drive")
    logger.info("=" * 60)
    
    # Target folder ID from the URL provided
    FOLDER_ID = "1T67sTJgCvz-PDSDS2NUnhPSTjhDXnscg"
    logger.info(f"🎯 Pasta alvo: {FOLDER_ID}")
    
    # Initialize Drive Handler
    logger.info("🔧 Inicializando DriveHandler...")
    drive_handler = DriveHandler()
    
    # Test different authentication methods
    auth_methods = []
    
    # Method 1: Check for environment API key
    env_api_key = os.getenv('GOOGLE_DRIVE_API_KEY')
    if env_api_key:
        auth_methods.append(("Environment API Key", env_api_key))
        logger.info("🔑 API Key encontrada no ambiente")
    else:
        logger.info("❌ Nenhuma API Key no ambiente")
    
    # Method 2: Check for credentials.json
    if os.path.exists('credentials.json'):
        auth_methods.append(("OAuth2 Credentials", 'credentials.json'))
        logger.info("📄 Arquivo credentials.json encontrado")
    else:
        logger.info("❌ Arquivo credentials.json não encontrado")
    
    # Method 3: Try without authentication (public access)
    auth_methods.append(("Public Access", None))
    
    logger.info(f"🧪 Testando {len(auth_methods)} métodos de autenticação...")
    logger.info("-" * 60)
    
    successful_auth = None
    
    for method_name, auth_data in auth_methods:
        logger.info(f"🔄 Testando: {method_name}")
        
        try:
            # Reset handler for each test
            drive_handler = DriveHandler()
            
            # Attempt authentication
            if method_name == "Environment API Key" or method_name.endswith("API Key"):
                success = drive_handler.authenticate_with_api_key(auth_data)
            elif method_name == "OAuth2 Credentials":
                success = drive_handler.authenticate_with_credentials(auth_data)
            elif method_name == "Public Access":
                # Try to build service without authentication
                try:
                    from googleapiclient.discovery import build
                    drive_handler.service = build('drive', 'v3')
                    success = True
                    logger.info("🔓 Tentando acesso público sem autenticação")
                except Exception as e:
                    success = False
                    logger.info(f"❌ Acesso público falhou: {e}")
            else:
                success = drive_handler.authenticate()
            
            if success:
                logger.info(f"✅ Autenticação bem-sucedida: {method_name}")
                
                # Test folder access
                logger.info("🧪 Testando acesso à pasta...")
                access_result = drive_handler.test_folder_access(FOLDER_ID)
                
                logger.info("📊 Resultado do teste de acesso:")
                for key, value in access_result.items():
                    logger.info(f"   {key}: {value}")
                
                if access_result['accessible']:
                    logger.info("🎉 SUCESSO! Pasta é acessível!")
                    successful_auth = method_name
                    
                    # Try to list some files
                    logger.info("📂 Listando arquivos da pasta...")
                    files = drive_handler.list_folder_contents(FOLDER_ID)
                    
                    if files:
                        logger.info(f"📄 Encontrados {len(files)} arquivos:")
                        for i, file in enumerate(files[:10]):  # Show first 10 files
                            name = file.get('name', 'Unknown')
                            mime_type = file.get('mimeType', 'Unknown')
                            size = file.get('size', 'Unknown')
                            logger.info(f"   {i+1}. {name} ({mime_type}) - {size} bytes")
                        
                        if len(files) > 10:
                            logger.info(f"   ... e mais {len(files) - 10} arquivos")
                    
                    # Ask if user wants to download files
                    print("\n" + "="*60)
                    print("🎉 CONEXÃO ESTABELECIDA COM SUCESSO!")
                    print(f"📁 Pasta: {access_result.get('folder_name', 'Desconhecida')}")
                    print(f"📊 Arquivos encontrados: {access_result['file_count']}")
                    print(f"🔑 Método de autenticação: {method_name}")
                    
                    response = input("\n❓ Deseja baixar todos os arquivos? (s/N): ").strip().lower()
                    
                    if response in ['s', 'sim', 'y', 'yes']:
                        logger.info("📥 Iniciando download de todos os arquivos...")
                        downloaded_files = drive_handler.process_folder(FOLDER_ID, download_all=True)
                        
                        if downloaded_files:
                            logger.info(f"🎉 Download concluído! {len(downloaded_files)} arquivos baixados")
                            logger.info("📁 Arquivos salvos em: data/materials/")
                            
                            # Show downloaded files
                            for file in downloaded_files:
                                logger.info(f"✅ {file.get('name')} ({file.get('size', 0)} bytes)")
                        else:
                            logger.warning("⚠️ Nenhum arquivo foi baixado")
                    else:
                        logger.info("ℹ️ Download cancelado pelo usuário")
                    
                    break
                else:
                    logger.warning(f"❌ Pasta não acessível com {method_name}: {access_result.get('error')}")
            else:
                logger.warning(f"❌ Falha na autenticação: {method_name}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar {method_name}: {str(e)}")
            logger.error(f"   Tipo do erro: {type(e).__name__}")
        
        logger.info("-" * 60)
    
    # Summary
    logger.info("📋 RESUMO DOS TESTES:")
    if successful_auth:
        logger.info(f"✅ Método bem-sucedido: {successful_auth}")
        logger.info("🎯 Recomendação: Use este método no sistema principal")
    else:
        logger.error("❌ Nenhum método de autenticação funcionou")
        logger.error("💡 Sugestões:")
        logger.error("   1. Verifique se a pasta é pública")
        logger.error("   2. Configure uma API Key válida")
        logger.error("   3. Configure o arquivo credentials.json com OAuth2")
        logger.error("   4. Verifique o ID da pasta")
    
    # Show final statistics
    stats = drive_handler.get_download_stats()
    logger.info(f"📊 Estatísticas finais:")
    logger.info(f"   Arquivos no diretório: {stats['total_files']}")
    logger.info(f"   Tamanho total: {stats['total_size']} bytes")
    logger.info(f"   Diretório: {stats['directory']}")

def check_credentials():
    """Check if credentials.json has the expected format"""
    if os.path.exists('credentials.json'):
        try:
            with open('credentials.json', 'r') as f:
                creds = json.load(f)
            
            logger.info("🔍 Analisando credentials.json...")
            
            if 'web' in creds:
                web = creds['web']
                logger.info("✅ Formato 'web' detectado")
                logger.info(f"   Client ID: {web.get('client_id', 'Missing')[:20]}...")
                logger.info(f"   Project ID: {web.get('project_id', 'Missing')}")
                logger.info(f"   Auth URI: {web.get('auth_uri', 'Missing')}")
                logger.info(f"   Token URI: {web.get('token_uri', 'Missing')}")
                return True
            elif 'installed' in creds:
                logger.info("✅ Formato 'installed' detectado")
                return True
            else:
                logger.error("❌ Formato de credentials.json não reconhecido")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao ler credentials.json: {e}")
            return False
    else:
        logger.info("❌ credentials.json não encontrado")
        return False

def show_setup_instructions():
    """Show setup instructions for Google Drive API"""
    print("\n" + "="*60)
    print("📖 INSTRUÇÕES DE CONFIGURAÇÃO")
    print("="*60)
    
    print("\n🔑 OPÇÃO 1: API Key (Recomendada para pastas públicas)")
    print("1. Vá para https://console.cloud.google.com/")
    print("2. Crie um projeto ou selecione um existente")
    print("3. Ative a Google Drive API")
    print("4. Crie uma API Key em 'Credentials'")
    print("5. Defina a variável de ambiente: GOOGLE_DRIVE_API_KEY=sua_api_key")
    
    print("\n🔐 OPÇÃO 2: OAuth2 (Para pastas privadas)")
    print("1. No Google Cloud Console, crie um OAuth2 Client ID")
    print("2. Baixe o arquivo JSON das credenciais")
    print("3. Renomeie para 'credentials.json' e coloque na pasta do projeto")
    
    print("\n📁 VERIFICANDO PASTA:")
    print("- URL: https://drive.google.com/drive/folders/1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ")
    print("- Verifique se a pasta é pública ou se você tem acesso")
    
    print("\n🚀 EXECUTAR TESTE:")
    print("python test_drive_connection.py")

if __name__ == "__main__":
    print("🚀 DNA da Força - Teste de Conexão Google Drive")
    print("="*60)
    
    # Check current setup
    logger.info("🔍 Verificando configuração atual...")
    check_credentials()
    
    # Show instructions
    show_setup_instructions()
    
    print("\n" + "="*60)
    response = input("❓ Deseja executar o teste agora? (s/N): ").strip().lower()
    
    if response in ['s', 'sim', 'y', 'yes']:
        main()
    else:
        print("ℹ️ Teste cancelado. Execute novamente quando estiver pronto.")
